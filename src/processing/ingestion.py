import os
from pathlib import Path
from config import DATA_PROCESSING_RAW_DIR, DEFAULT_MIN_PHOTO_ERROR, DEFAULT_MIN_PHOTO_WARNING, SUPPORTED_INPUT_FORMATS
from src.models.captured_image import CapturedImage
from src.core.exceptions import FolderNotFoundError, FolderAccessError, IngestionError
from src.utils.log_utils import success_alert, warning_alert

def get_raw_captured_images(input_dir: Path = DATA_PROCESSING_RAW_DIR):
    """
    Funzione che restituisce una lista di istanze CapturedImage prese dalla cartella RAW_IMAGES_DIR

    Returns:
        list[CapturedImage]: Una lista di oggetti CapturedImage pronti per la pipeline di processing.

    Raises:
        IngestionError
    """

    raw_captured_images = []

    if not input_dir.exists():
        raise IngestionError('Input dir not found.')
    
    if not os.access(input_dir, os.R_OK | os.X_OK):
        raise IngestionError('Permission denied.')
    
    for raw_captured_image_name in os.listdir(input_dir):
        if raw_captured_image_name.lower().endswith(SUPPORTED_INPUT_FORMATS):
            raw_captured_image = CapturedImage(str(input_dir / raw_captured_image_name))
            raw_captured_images.append(raw_captured_image)

    if len(raw_captured_images) <= DEFAULT_MIN_PHOTO_WARNING: warning_alert('Less than 15 images detected in the project folder.')

    if len(raw_captured_images) <= DEFAULT_MIN_PHOTO_ERROR: raise IngestionError('Insufficient photos detected.')

    success_alert('Ingestion completed.')

    return raw_captured_images
    
