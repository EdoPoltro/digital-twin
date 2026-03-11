import json
from pathlib import Path
from config import INTERIM_IMAGES_DIR, PROCESSED_IMAGES_DIR, RAW_IMAGES_DIR
from models.image_data import CapturedImage, ImageStatus
from utils.exceptions import EmptyDatasetError, EnvSetupError, FileAccessError, FileNotFoundError, ImageCopyError
import shutil

def open_json(file_path: Path) -> dict:
    """
    Legge un file JSON dal disco e restituisce un dizionario.

    Args:
        file_path (Path): percorso del file

    Raises:
        FileNotFoundError
        FileAccessError

    Returns:
        dict
    """
    if not file_path.exists():
        raise FileNotFoundError(file_path)
    try:
        with open(file_path, "r", encoding="utf-8") as file:
            return json.load(file)
    except (json.JSONDecodeError, PermissionError) as e:
        raise FileAccessError(file_path, e)
    
def setup_project_environment(directories: list[Path]):
    for dir in directories:
        if dir.exists():
            try:
                shutil.rmtree(dir)
                dir.mkdir(parents=True, exist_ok=True)
            except OSError as e:
                raise EnvSetupError(str(dir))
        else:
            dir.mkdir(parents=True, exist_ok=True)

def get_target_dir(promotion_status: ImageStatus) -> Path:
    """
    Funzione che ritorna la cartella target in base allo stato delle immagini

    Args:
        promotion_status (ImageStatus): lista da spostare

    Returns:
        Path
    """
    match promotion_status:
        case ImageStatus.RAW:
            return RAW_IMAGES_DIR
        case ImageStatus.INTERIM:
            return INTERIM_IMAGES_DIR
        case ImageStatus.PROCESSED:
            return PROCESSED_IMAGES_DIR
    
def promote_captured_image(captured_image: CapturedImage, target_dir: Path, promotion_status: ImageStatus) -> None:
    """
    Funzione che gestisce la promozione dello stato di una lista di immagini

    Args:
        caputerd_image (CapturedImage): lista da spostare
        promotion_status (ImageStatus): stato finale della immagine
        target_dir (Path): directory di destinazione

    Raises:
        ImageCopyError
    """
    try:
        target_path = target_dir / captured_image.file_name
        shutil.copy2(captured_image.file_path, target_path) # genera esception

        captured_image.status = promotion_status
        captured_image.update_file_path(target_dir)
    except (OSError) as e:
        raise ImageCopyError(captured_image.file_path,'Copy error')
    
def promote_captured_images(captured_images: list[CapturedImage], promotion_status: ImageStatus) -> None:
    """
    Funzione che gestisce la promozione dello stato di una lista di immagini e le copia 

    Args:
        caputerd_images (list[CapturedImage]): lista da spostare
        promotion_status (ImageStatus): stato finale della immagine

    Raises:
        EmptyDatasetError
    """
    if promotion_status in [ImageStatus.ERROR, ImageStatus.RAW]: return # capire se fare una exception

    target_dir = get_target_dir(promotion_status)
    target_dir.mkdir(parents=True, exist_ok=True)

    counter = 0

    for captured_image in captured_images:
        if captured_image.status in [ImageStatus.ERROR, promotion_status]: continue
        try:
            promote_captured_image(captured_image, target_dir, promotion_status)
            counter += 1
        except (ImageCopyError) as e:
            print(e)

    if counter == 0: raise EmptyDatasetError(step_name='Images copy')