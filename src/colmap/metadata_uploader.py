from pathlib import Path
from typing import Literal
from src.utils.log_utils import success_alert
from config import DATA_COLMAP_DEFAULT_CAMERAS_DATABASE, DATA_COLMAP_DEFAULT_GPS_DATA, DEFAULT_MIN_PHOTO_ERROR, DEFAULT_MIN_PHOTO_WARNING, DEFAULT_SCAN_MODE
from src.models.captured_image import CameraMetadata, CapturedImage, ImageStatus, SpatialMetadata
from src.core.exceptions import MetadataUploaderError
from src.utils.io_utils import init_sqlite_connection, write_text_to_file
from src.utils.log_utils import warning_alert
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

def start_camera_metadata_uploading(captured_images: list[CapturedImage], cameras_db_path: Path = DATA_COLMAP_DEFAULT_CAMERAS_DATABASE):
    """
    Funzione per il caricamento dei dati delle focali nel database

    Args: 
        captured_images (list[CapturedImages])
        cameras_db_path (Path)

    Raises:
        MetadataUploaderError
    """
    errors = 0

    colmap_db_conn = init_sqlite_connection(cameras_db_path)
    cursor = colmap_db_conn.cursor()
    setup_colmap_tables(cursor)
    
    for id, captured_image in  enumerate(captured_images, start=1):
        try:
            if captured_image.status == ImageStatus.ERROR: continue
            _upload_captured_image_camera_data(captured_image.camera_metadata, captured_image.file_name, id, cursor)
            
        except Exception as e:
            captured_image.status = ImageStatus.ERROR
            errors += 1
            warning_alert(f'Camera metadata uploading failed for photo {captured_image.file_name}, {e}.')    
        
    if errors > 0: warning_alert(f'{errors} cameras uploading failed.')
    
    if len(captured_images) - errors < DEFAULT_MIN_PHOTO_WARNING: warning_alert("Less than 15 cameras metadata uploaded.")

    if len(captured_images) - errors < DEFAULT_MIN_PHOTO_ERROR: raise MetadataUploaderError('Insufficient cameras metadata uploaded.')

    success_alert(f'Cameras metadata uploading completed.')
    
    colmap_db_conn.commit()
    colmap_db_conn.close()

def start_gps_metadata_uploading(captured_images: list[CapturedImage], gps_txt_path: Path = DATA_COLMAP_DEFAULT_GPS_DATA, scan_mode: Literal['indoor','outdoor'] = DEFAULT_SCAN_MODE):
    """
    Funzione per il caricamento dei dati gps nel file txt 

    Args: 
        captured_images (list[CapturedImages])
        gps_txt_path (Path)

    Raises:
        MetadataUploaderError
    """
    errors = 0

    gps_data_block: list[str] = []

    for captured_image in captured_images:
        try:
            if captured_image.status == ImageStatus.ERROR: continue
            gps_data = _upload_captured_image_gps_data(captured_image.spatial_metadata, captured_image.file_name)
            gps_data_block.append(gps_data)
            
        except Exception as e: 
            if scan_mode == 'indoor': captured_image.status = ImageStatus.ERROR
            errors += 1
            warning_alert(f'GPS metadata uploading failed for photo {captured_image.file_name}, {e}.')

    if errors > 0: warning_alert(f'{errors} GPS uploading failed.')

    if len(captured_images) - errors <= DEFAULT_MIN_PHOTO_WARNING: warning_alert('Less than 15 GPS metadata uploaded.')

    if len(captured_images) - errors <= DEFAULT_MIN_PHOTO_ERROR: raise MetadataUploaderError('Insufficient GPS metadata uploaded.')

    write_text_to_file(gps_txt_path, "".join(gps_data_block))

    success_alert(f'GPS metadata uploading completed.')

def start_full_metadata_uploading(captured_images: list[CapturedImage], cameras_db_path: Path = DATA_COLMAP_DEFAULT_CAMERAS_DATABASE, gps_txt_path: Path = DATA_COLMAP_DEFAULT_GPS_DATA, scan_mode: Literal['indoor', 'outdoor'] = DEFAULT_SCAN_MODE):
    """
    Funzione per il caricamento dei dati gps e delle focali

    Args: 
        captured_images (list[CapturedImages])
        cameras_db_path (Path)
        gps_txt_path (Path)

    Raises:
        MetadataUploaderError
    """
    start_camera_metadata_uploading(captured_images, cameras_db_path)
    if scan_mode == 'outdoor': start_gps_metadata_uploading(captured_images, gps_txt_path)

