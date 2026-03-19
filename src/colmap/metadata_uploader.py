from pathlib import Path
import subprocess
from typing import Literal
from src.utils.logging_utils import CLR_WARNING
from config import DATA_COLMAP_DEFAULT_CAMERAS_DATABASE, DATA_COLMAP_DEFAULT_GPS_DATA, DEFAULT_SCAN_MODE
from src.models.captured_image import CameraMetadata, CapturedImage, ImageStatus, SpatialMetadata
from src.core.exceptions import UploadingMetadataError
from src.utils.helpers_io import init_sqlite_connection, write_text_to_file
from src.utils.logging_utils import warning_alert
import sqlite3
import numpy as np

def setup_colmap_tables(cursor: sqlite3.Cursor):
    """Crea le tabelle con lo schema esatto richiesto da COLMAP."""
    cursor.execute("CREATE TABLE cameras (camera_id INTEGER PRIMARY KEY AUTOINCREMENT NOT NULL, model INTEGER NOT NULL, width INTEGER NOT NULL, height INTEGER NOT NULL, params BLOB, prior_focal_length INTEGER NOT NULL)")
    cursor.execute("CREATE TABLE images (image_id INTEGER PRIMARY KEY AUTOINCREMENT NOT NULL, name TEXT NOT NULL, camera_id INTEGER NOT NULL, prior_qw REAL, prior_qx REAL, prior_qy REAL, prior_qz REAL, prior_tx REAL, prior_ty REAL, prior_tz REAL)")

def _upload_captured_image_camera_data(camera_metadata: CameraMetadata, file_name: str, camera_id: int, cursor: sqlite3.Cursor):
    """
    Funzione che carica sul databse i dati della camera in un database sqlite per comunicare con colmap

    Args: 
        camera_metadata: (CameraMetadata)
        file_name (str)
        id (int)
        cursor (sqlite3.Cursor)
    """
    width = camera_metadata.resolution[0]
    height = camera_metadata.resolution[1]
    focal_mm = camera_metadata.focal_length
    
    max_res = max(width, height)
    max_sensor = max(camera_metadata.sensor_size) 
    
    focal_px = max_res * (focal_mm / max_sensor) if max_sensor > 0 else max_res * 1.2
    cx = width / 2.0
    cy = height / 2.0
    
    params_array = np.array([focal_px, cx, cy, 0.0], dtype=np.float64)
    params_blob = params_array.tobytes()
    
    cursor.execute(
        """
        INSERT INTO cameras (camera_id, model, width, height, params, prior_focal_length) 
        VALUES (?, ?, ?, ?, ?, ?)
        """,
        (camera_id, 2, width, height, sqlite3.Binary(params_blob), 1)
    )
    
    cursor.execute(
        """
        INSERT INTO images (image_id, name, camera_id) 
        VALUES (?, ?, ?)
        """,
        (camera_id, file_name, camera_id)
    )

def _upload_captured_image_gps_data(spatial_metadata: SpatialMetadata, file_name: str) -> str:
    """
    Funzione che dati i dati gps di un immagine prepara la stringa per il file DATA_COLMAP_DEFAULT_GPS_DATA

    Args:
        spatial_metadata (SpatialMetadata)
        file_name (str)

    Returns:
        str
    """
    if not any([spatial_metadata.altitude, spatial_metadata.longitude, spatial_metadata.latitude]):
        raise Exception()

    gps_row = f"{file_name} {spatial_metadata.latitude:.6f} {spatial_metadata.longitude:.6f} {spatial_metadata.altitude:.2f}\n".replace(',', '.')
    return gps_row

def _start_camera_metadata_uploading(captured_images: list[CapturedImage], cameras_db_path: Path = DATA_COLMAP_DEFAULT_CAMERAS_DATABASE):
    """
    Funzione per il caricamento dei dati delle focali nel database

    Args: 
        captured_images (list[CapturedImages])
        cameras_db_path (Path)

    Raises:
        UploadingMetadataError
    """
    counter = 0

    colmap_db_conn = init_sqlite_connection(cameras_db_path)
    cursor = colmap_db_conn.cursor()
    setup_colmap_tables(cursor)
    
    for id, captured_image in  enumerate(captured_images, start=1):
        try:
            if captured_image.status == ImageStatus.ERROR: continue
            _upload_captured_image_camera_data(captured_image.camera_metadata, captured_image.file_name, id, cursor)
            counter += 1
        except Exception:
            raise UploadingMetadataError(f"Error loading camera data for image {captured_image.file_name}, potential data misalignment.", CLR_WARNING)     
    
    if counter < 15: warning_alert("Database contains fewer than 15 images. Processing might fail or be inaccurate.")

    if counter == 0: raise UploadingMetadataError("No cameras metadata uploaded.")
    
    colmap_db_conn.commit()
    colmap_db_conn.close()

def _start_gps_metadata_uploading(captured_images: list[CapturedImage], gps_txt_path: Path = DATA_COLMAP_DEFAULT_GPS_DATA):
    """
    Funzione per il caricamento dei dati gps nel file txt 

    Args: 
        captured_images (list[CapturedImages])
        gps_txt_path (Path)

    Raises:
        UploadingMetadataError
    """
    counter = 0

    gps_data_block: list[str] = []

    for captured_image in captured_images:
        try:
            if captured_image.status == ImageStatus.ERROR: continue
            gps_data = _upload_captured_image_gps_data(captured_image.spatial_metadata, captured_image.file_name)
            gps_data_block.append(gps_data)
            counter += 1
        except Exception: 
            raise UploadingMetadataError(f"Error loading GPS data for image {captured_image.file_name}, potential data misalignment.", CLR_WARNING)

    if counter < 15: warning_alert("Database contains fewer than 15 images. Processing might fail or be inaccurate.")

    if counter == 0: raise UploadingMetadataError("No GPS metadata uploaded.")

    write_text_to_file(gps_txt_path, "".join(gps_data_block))

def start_full_metadata_uploading(captured_images: list[CapturedImage], cameras_db_path: Path = DATA_COLMAP_DEFAULT_CAMERAS_DATABASE, gps_txt_path: Path = DATA_COLMAP_DEFAULT_GPS_DATA, scan_mode: Literal['indoor', 'outdoor'] = DEFAULT_SCAN_MODE):
    """
    Funzione per il caricamento dei dati gps e delle focali

    Args: 
        captured_images (list[CapturedImages])
        cameras_db_path (Path)
        gps_txt_path (Path)

    Raises:
        UploadingMetadataError
    """
    valid_images = [img for img in captured_images if img.status != ImageStatus.ERROR] # per disallinemanto
    _start_camera_metadata_uploading(valid_images, cameras_db_path)
    if scan_mode == 'outdoor': _start_gps_metadata_uploading(valid_images, gps_txt_path)

