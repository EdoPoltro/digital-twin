from pathlib import Path
import subprocess
from config import COLMAP_DB_DATA, COLMAP_EXE, COLMAP_GPS_DATA, COLMAP_SPARSE_DIR, PROCESSED_IMAGES_DIR
from models.image_data import CameraMetadata, CapturedImage, ImageStatus, SpatialMetadata
from utils.helpers_io import init_sqlite_connection, write_text_to_file
from utils.logging_utils import error_alert, warning_alert
import sqlite3
import numpy as np

def run_feature_extractor(colmap_exe: Path, db_path: Path, images_dir: Path):
    """
    Fase 1: Trova i punti chiave nelle immagini usando il database pre-compilato.
    """
    # log_info("Avvio Estrazione Feature...")
    
    command = [
        str(colmap_exe), "feature_extractor",
        "--database_path", str(db_path),
        "--image_path", str(images_dir),
        "--FeatureExtraction.use_gpu", "0",
        "--FeatureExtraction.num_threads", "2" # per le performance
    ]
    
    # Esegue il comando e blocca il codice finché non ha finito
    subprocess.run(command, check=True)

def run_mapper(colmap_exe: Path, db_path: Path, images_dir: Path, output_dir: Path):
    """
    Fase 3: Ricostruzione 3D (Structure from Motion).
    Genera la nuvola di punti e la posizione delle fotocamere nello spazio.
    """
    # Assicuriamoci che la cartella di destinazione esista, altrimenti COLMAP si arrabbia
    output_dir.mkdir(parents=True, exist_ok=True)
    
    command = [
        str(colmap_exe), "mapper",
        "--database_path", str(db_path),
        "--image_path", str(images_dir),
        "--output_path", str(output_dir)
    ]
    
    # Questa fase può richiedere da qualche minuto a diverse ore a seconda delle foto!
    subprocess.run(command, check=True)

def run_sequential_matcher(colmap_exe: Path, db_path: Path, overlap: int = 10):
    """
    Fase 2: Trova le corrispondenze tra i punti delle foto vicine nel tempo.
    
    Args:
        overlap: Numero di foto successive/precedenti con cui confrontare ogni scatto.
    """
    # log_info(f"Avvio Matching Sequenziale (Overlap: {overlap} foto)...")
    
    command = [
        str(colmap_exe), "sequential_matcher",
        "--database_path", str(db_path),
        "--SequentialMatching.overlap", str(overlap),
        "--FeatureMatching.use_gpu", "0"
    ]
    
    subprocess.run(command, check=True)
    # log_success("Matching completato con successo.")

def setup_colmap_tables(cursor: sqlite3.Cursor):
    """Crea le tabelle con lo schema esatto richiesto da COLMAP."""
    cursor.execute("CREATE TABLE cameras (camera_id INTEGER PRIMARY KEY AUTOINCREMENT NOT NULL, model INTEGER NOT NULL, width INTEGER NOT NULL, height INTEGER NOT NULL, params BLOB, prior_focal_length INTEGER NOT NULL)")
    cursor.execute("CREATE TABLE images (image_id INTEGER PRIMARY KEY AUTOINCREMENT NOT NULL, name TEXT NOT NULL, camera_id INTEGER NOT NULL, prior_qw REAL, prior_qx REAL, prior_qy REAL, prior_qz REAL, prior_tx REAL, prior_ty REAL, prior_tz REAL)")

def upload_captured_image_camera_data(camera_metadata: CameraMetadata, file_name: str, camera_id: int, cursor: sqlite3.Cursor):
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
    
    # Calcolo focale
    focal_px = max_res * (focal_mm / max_sensor) if max_sensor > 0 else max_res * 1.2
    cx = width / 2.0
    cy = height / 2.0
    
    # ---------------- LA MAGIA BINARIA ----------------
    # 1. Creiamo un array NumPy forzandolo a float64 (double)
    params_array = np.array([focal_px, cx, cy, 0.0], dtype=np.float64)
    
    # 2. Lo trasformiamo in byte puri (BLOB)
    params_blob = params_array.tobytes()
    # --------------------------------------------------
    
    cursor.execute(
        """
        INSERT INTO cameras (camera_id, model, width, height, params, prior_focal_length) 
        VALUES (?, ?, ?, ?, ?, ?)
        """,
        # Passiamo i byte puri protetti da sqlite3.Binary
        (camera_id, 2, width, height, sqlite3.Binary(params_blob), 1)
    )
    
    cursor.execute(
        """
        INSERT INTO images (image_id, name, camera_id) 
        VALUES (?, ?, ?)
        """,
        (camera_id, file_name, camera_id)
    )

def upload_captured_image_gps_data(spatial_metadata: SpatialMetadata, file_name: str) -> str:
    """
    Funzione che dati i dati gps di un immagine prepara la stringa per il file COLMAP_GPS_DATA

    Args:
        spatial_metadata (SpatialMetadata)
        file_name (str)

    Returns:
        str
    """
    if not any([spatial_metadata.longitude, spatial_metadata.altitude, spatial_metadata.latitude]):
        raise Exception('errore')
    
    gps_row = f'{file_name} {spatial_metadata.longitude} {spatial_metadata.latitude} {spatial_metadata.altitude}\n'
    return gps_row

def upload_captured_images_metadata(captured_images: list[CapturedImage]):
    """
    Funzione che gestisce la scrittura dei metadati di una lista di immagini già processate per
    usarle in colmap.

    Args:
        captured_images (list[CapturedImage]): lista di immagini da caricare

    Raises:
    """
    counter = 0

    gps_data_block: list[str] = []
    colmap_db_conn = init_sqlite_connection(COLMAP_DB_DATA)
    cursor = colmap_db_conn.cursor()
    setup_colmap_tables(cursor)

    for id, captured_image in enumerate(captured_images, start=1):

        if captured_image.status == ImageStatus.ERROR: continue

        try:
            upload_captured_image_camera_data(captured_image.camera_metadata, captured_image.file_name, id, cursor)
            gps_data = upload_captured_image_gps_data(captured_image.spatial_metadata, captured_image.file_name)
            gps_data_block.append(gps_data)

            counter += 1
        except Exception as e: # da rendere piu rigoroso
            warning_alert(f'There was a problem loading file {captured_image.file_name}.') # mettere exception

    if counter == 0: error_alert('No data was successfully loaded.') # forse meglio exception

    write_text_to_file(COLMAP_GPS_DATA, "".join(gps_data_block))
    colmap_db_conn.commit()
    colmap_db_conn.close()

    try:
        run_feature_extractor(COLMAP_EXE, COLMAP_DB_DATA, PROCESSED_IMAGES_DIR)
        run_sequential_matcher(COLMAP_EXE, COLMAP_DB_DATA)
        run_mapper(COLMAP_EXE, COLMAP_DB_DATA, PROCESSED_IMAGES_DIR, COLMAP_SPARSE_DIR)
    except Exception as e:
        error_alert(f"Errore fatale durante l'esecuzione di COLMAP: {e}")