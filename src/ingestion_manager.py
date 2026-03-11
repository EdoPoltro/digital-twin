import os
from config import RAW_IMAGES_DIR, SUPPORTED_INPUT_FORMATS
from models.image_data import CapturedImage
from utils.exceptions import FolderNotFoundError, FolderAccessError

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

    if not RAW_IMAGES_DIR.exists():
        raise FolderNotFoundError(RAW_IMAGES_DIR)
    
    if not os.access(RAW_IMAGES_DIR, os.R_OK | os.X_OK):
        raise FolderAccessError(RAW_IMAGES_DIR)
    
    for raw_captured_image_name in os.listdir(RAW_IMAGES_DIR):
        if raw_captured_image_name.lower().endswith(SUPPORTED_INPUT_FORMATS):
            raw_captured_image = CapturedImage(str(RAW_IMAGES_DIR / raw_captured_image_name))
            raw_captured_images.append(raw_captured_image)
        
    return raw_captured_images
    
