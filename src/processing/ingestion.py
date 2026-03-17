import os
from config import DATA_PROCESSING_RAW_DIR, SUPPORTED_INPUT_FORMATS
from src.models.captured_image import CapturedImage
from src.core.exceptions import FolderNotFoundError, FolderAccessError

def get_raw_captured_images():
    """
    Funzione che restituisce una lista di istanze CapturedImage prese dalla cartella RAW_IMAGES_DIR

    Returns:
        list[CapturedImage]: Una lista di oggetti CapturedImage pronti per la pipeline di processing.

    Raises:
        FolderNotFoundError: Se la cartella di input non esiste.
        PermissionError: Se non si hanno i permessi di lettura sulla cartella.
    """

    raw_captured_images = []

    if not DATA_PROCESSING_RAW_DIR.exists():
        raise FolderNotFoundError(DATA_PROCESSING_RAW_DIR)
    
    if not os.access(DATA_PROCESSING_RAW_DIR, os.R_OK | os.X_OK):
        raise FolderAccessError(DATA_PROCESSING_RAW_DIR)
    
    for raw_captured_image_name in os.listdir(DATA_PROCESSING_RAW_DIR):
        if raw_captured_image_name.lower().endswith(SUPPORTED_INPUT_FORMATS):
            raw_captured_image = CapturedImage(str(DATA_PROCESSING_RAW_DIR / raw_captured_image_name))
            raw_captured_images.append(raw_captured_image)
        
    return raw_captured_images
    
