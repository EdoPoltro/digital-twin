import cv2
from cv2.typing import MatLike
import numpy as np
from pathlib import Path
from typing import Literal
from config import DATA_PROCESSING_INTERIM_DIR, DATA_PROCESSING_PROCESSED_DIR, DATA_PROCESSING_RAW_DIR, DEFAULT_ENVIRONMENT_MODE
from src.core.exceptions import ProcessorError
from src.models.captured_image import CapturedImage, ImageStatus
from src.processing.promoter import promote_captured_images
from src.utils.log_utils import success_alert, warning_alert

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
        if self.environment == 'standard': self.start_standard_piepeline()
        elif self.environment == 'underwater': self.start_underwater_pipeline()

    def start_standard_piepeline(self):
        """
        Funzione dedicata alla pipeline standard.
        """
        for captured_image in self.captured_images:
            captured_image.status = ImageStatus.INTERIM
            image = cv2.imread(str(captured_image.file_path))
            if image is None:
                captured_image.status = ImageStatus.ERROR
                warning_alert(f'Failed to process image {captured_image.file_name}.')
                continue

            image_clahe = self._run_soft_clahe(image)
            image_final = self._run_sharpening(image_clahe)

            output_path = self.processed_dir / captured_image.file_name
            cv2.imwrite(str(output_path), image_final)
            
        self.captured_images = promote_captured_images(self.captured_images, ImageStatus.PROCESSED)
        success_alert('Standard processor pipeline completed.')

    def _run_soft_clahe(self, image: MatLike):
        """
        Funzione che inserisce un leggero contrasto nella foto.
        """
        lab = cv2.cvtColor(image, cv2.COLOR_BGR2LAB)
        l_channel, a_channel, b_channel = cv2.split(lab)
        clahe = cv2.createCLAHE(clipLimit=2.0, tileGridSize=(8, 8))
        cl = clahe.apply(l_channel)
        limg = cv2.merge((cl, a_channel, b_channel))
        return cv2.cvtColor(limg, cv2.COLOR_LAB2BGR)

    def _run_sharpening(self, image: MatLike):
        """
        Funzione che rende i bordi più accentuati.
        """
        kernel = np.array([[ 0, -1,  0], [-1,  5, -1], [ 0, -1,  0]])
        return cv2.filter2D(image, -1, kernel)

    def start_underwater_pipeline(self):
        """
        Funzione dedicata alla pipeline sottacqua.
        """
        pass

    def _run_red_channel_boost(self):
        """
        Funzione che aggiunge del rosso.
        """
        pass

    def _run_denoising(self):
        """
        Funzione che rimuove il colore.
        """
        pass

    def _run_hard_clahe(self):
        """
        Funzione che inserisce un forte contrasto nella foto.
        """
        pass

    def get_captured_images(self) -> list[CapturedImage]:
        return self.captured_images