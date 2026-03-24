import cv2
from cv2.typing import MatLike
import numpy as np
from pathlib import Path
from typing import Callable, Literal
from config import DATA_PROCESSING_PROCESSED_DIR, DATA_PROCESSING_RAW_DIR, DEFAULT_ENVIRONMENT_MODE, DEFAULT_MIN_PHOTO_ERROR, DEFAULT_MIN_PHOTO_WARNING
from src.core.exceptions import ProcessorError
from src.models.captured_image import CapturedImage, ImageStatus
from src.processing.promoter import promote_captured_images
from src.utils.log_utils import progress_bar, success_alert, warning_alert

class ProcessorManager:

    def __init__(self, raw_captured_images: list[CapturedImage], environment: Literal['standard', 'underwater'] = DEFAULT_ENVIRONMENT_MODE, raw_dir: Path = DATA_PROCESSING_RAW_DIR, processed_dir: Path = DATA_PROCESSING_PROCESSED_DIR):
        self.captured_images = raw_captured_images
        self.raw_dir = raw_dir
        self.processed_dir = processed_dir
        self.environment = environment

        self._run_constructor_validator()

    def _run_constructor_validator(self):
        if not self.raw_dir.exists():
            raise ProcessorError('Input dir not found')
        self.processed_dir.parent.mkdir(parents=True, exist_ok=True)
        
    def start_full_processing(self):
        """
        Funzione per gestire la scelta automatica della pipeline da seguire.
        """
        if self.environment == 'standard': self.start_standard_pipeline()
        elif self.environment == 'underwater': self.start_underwater_pipeline()

    def start_standard_pipeline(self):
        self._pipeline_wrapper(
            lambda img: self._run_sharpening(self._run_soft_clahe(img)), 
            'Standard'
        )

    def start_underwater_pipeline(self):
        """
        Funzione dedicata alla pipeline sottacqua.
        """
        self._pipeline_wrapper(
            lambda img: self._run_hard_clahe(self._run_denoising(self._run_red_channel_boost(img))), 
            'Underwater'
        )

    def _pipeline_wrapper(self, filter_function: Callable[[MatLike], MatLike], pipeline_name: str):
        """
        Funzione dedicata alla pipeline standard.
        """
        errors = 0

        for captured_image in progress_bar(self.captured_images, f"Running {pipeline_name} processing Pipeline"):
            try:
                captured_image.status = ImageStatus.INTERIM
                image = cv2.imread(str(captured_image.file_path))
                if image is None:
                    raise Exception('Read failed')

                image_final = filter_function(image)

                output_path = self.processed_dir / captured_image.file_name
                cv2.imwrite(str(output_path), image_final)
            except Exception as e:
                warning_alert(f'Processing failed for photo {captured_image.file_name}')
                captured_image.status = ImageStatus.ERROR
                errors += 1

        if errors > 0: warning_alert(f'{errors} photos removed.')

        if len(self.captured_images) - errors <= DEFAULT_MIN_PHOTO_ERROR: raise ProcessorError('Insufficient photos processed.')

        if len(self.captured_images) - errors <= DEFAULT_MIN_PHOTO_WARNING: warning_alert(f'Less than {DEFAULT_MIN_PHOTO_WARNING} images processed.')
    
        self.captured_images = promote_captured_images(self.captured_images, ImageStatus.PROCESSED, move=False)

        success_alert(f'{pipeline_name.capitalize()} processing pipeline completed.')

    def _run_soft_clahe(self, image: MatLike) -> MatLike:
        """
        Funzione che inserisce un leggero contrasto nella foto.
        """
        lab = cv2.cvtColor(image, cv2.COLOR_BGR2LAB)
        l_channel, a_channel, b_channel = cv2.split(lab)
        clahe = cv2.createCLAHE(clipLimit=2.0, tileGridSize=(8, 8))
        cl = clahe.apply(l_channel)
        limg = cv2.merge((cl, a_channel, b_channel))
        return cv2.cvtColor(limg, cv2.COLOR_LAB2BGR)

    def _run_sharpening(self, image: MatLike) -> MatLike:
        """
        Funzione che rende i bordi più accentuati.
        """
        kernel = np.array([[ 0, -1,  0], [-1,  5, -1], [ 0, -1,  0]])
        return cv2.filter2D(image, -1, kernel)

    def _run_red_channel_boost(self, image: MatLike) -> MatLike:
        """
        Funzione che aggiunge del rosso.
        """
        b, g, r = cv2.split(image)
        r_boosted = cv2.addWeighted(r, 1.3, np.zeros_like(r), 0, 0)
        return cv2.merge((b, g, r_boosted))

    def _run_denoising(self, image: MatLike) -> MatLike:
        """
        Funzione che rimuove il colore.
        """
        return cv2.fastNlMeansDenoisingColored(image, None, h=10, hColor=10, templateWindowSize=7, searchWindowSize=21)

    def _run_hard_clahe(self, image: MatLike) -> MatLike:
        """
        Funzione che inserisce un forte contrasto nella foto.
        """
        lab = cv2.cvtColor(image, cv2.COLOR_BGR2LAB)
        l_channel, a_channel, b_channel = cv2.split(lab)
        clahe = cv2.createCLAHE(clipLimit=4.5, tileGridSize=(8, 8))
        cl = clahe.apply(l_channel)
        limg = cv2.merge((cl, a_channel, b_channel))
        return cv2.cvtColor(limg, cv2.COLOR_LAB2BGR)

    def get_captured_images(self) -> list[CapturedImage]:
        return self.captured_images