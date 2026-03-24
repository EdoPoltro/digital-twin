
from pathlib import Path
from config import DATA_PROCESSING_INTERIM_DIR, DATA_PROCESSING_PROCESSED_DIR, DATA_PROCESSING_RAW_DIR, DEFAULT_MIN_PHOTO_ERROR, DEFAULT_MIN_PHOTO_WARNING
from src.models.captured_image import CapturedImage, ImageStatus
from src.core.exceptions import EmptyDatasetError,ImageCopyError, PromoterError
import shutil
from pathlib import Path

from src.utils.log_utils import success_alert, warning_alert

def remove_error_images(captured_images: list[CapturedImage]) -> list[CapturedImage]:
    return list(filter(lambda img: img.status is not ImageStatus.ERROR, captured_images))

def _get_target_dir(promotion_status: ImageStatus) -> Path:
    """
    Funzione che ritorna la cartella target in base allo stato delle immagini

    Args:
        promotion_status (ImageStatus): lista da spostare

    Returns:
        Path
    """
    match promotion_status:
        case ImageStatus.RAW:
            return DATA_PROCESSING_RAW_DIR
        case ImageStatus.INTERIM:
            return DATA_PROCESSING_INTERIM_DIR
        case ImageStatus.PROCESSED:
            return DATA_PROCESSING_PROCESSED_DIR
    
def promote_captured_image(captured_image: CapturedImage, target_dir: Path, promotion_status: ImageStatus, move: bool = True) -> None:
    """
    Funzione che gestisce la promozione dello stato di una lista di immagini

    Args:
        caputerd_image (CapturedImage): lista da spostare
        promotion_status (ImageStatus): stato finale della immagine
        target_dir (Path): directory di destinazione

    """
    target_path = target_dir / captured_image.file_name
    if move: shutil.copy2(captured_image.file_path, target_path)
    captured_image.status = promotion_status
    captured_image.update_file_path(target_dir)

    
def promote_captured_images(captured_images: list[CapturedImage], promotion_status: ImageStatus, move: bool = True) -> list[CapturedImage]:
    """
    Funzione che gestisce la promozione dello stato di una lista di immagini e le copia 

    Args:
        caputerd_images (list[CapturedImage]): lista da spostare
        promotion_status (ImageStatus): stato finale della immagine

    Raises:
        PromoterError

    Returns:
        list[CapturedImage]
    """
    if promotion_status in [ImageStatus.ERROR, ImageStatus.RAW]: 
        raise PromoterError('Invalid promotion state.')

    target_dir = _get_target_dir(promotion_status)
    target_dir.mkdir(parents=True, exist_ok=True)

    errors = 0

    for captured_image in captured_images:
        if captured_image.status in [ImageStatus.ERROR, promotion_status]: continue
        try:
            promote_captured_image(captured_image, target_dir, promotion_status, move=move)
        except Exception as e:
            captured_image.status = ImageStatus.ERROR
            errors += 1
            warning_alert(f'Metadata extraction failed for photo {captured_image.file_name}, {e}.')

    output_captured_images = remove_error_images(captured_images)

    if errors > 0: warning_alert(f'{errors} photos removed.')

    if len(output_captured_images) <= DEFAULT_MIN_PHOTO_ERROR: raise PromoterError('Insufficient photos detected.')

    if len(output_captured_images) <= DEFAULT_MIN_PHOTO_WARNING: warning_alert(f'Less than {DEFAULT_MIN_PHOTO_WARNING} images detected in the project folder.')

    success_alert(f'Promotion to state {promotion_status} completed.')

    return output_captured_images