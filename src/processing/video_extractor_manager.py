from pathlib import Path

import cv2
import numpy
from src.core.exceptions import VideoExtractorError
from config import (
    DATA_PROCESSING_RAW_DIR, 
    DATA_PROCESSING_VIDEO_PATH,
    DEFAULT_MIN_PHOTO_ERROR,
    DEFAULT_MIN_PHOTO_WARNING,
    SUPPORTED_VIDEO_FORMATS, 
    VIDEO_MIN_DIFFERENCE, 
    VIDEO_MIN_SHARPNESS, 
    VIDEO_SAMPLE_INTERVAL
)
from src.utils.log_utils import progress_bar, success_alert, warning_alert

class VideoExtractorManager:
    """
    Manager che gestisce l'estrazione delle foto dal video.
    """
    def __init__(
            self, 
            video_path: Path = DATA_PROCESSING_VIDEO_PATH,
            output_dir: Path = DATA_PROCESSING_RAW_DIR,    
            min_sharpness: float = VIDEO_MIN_SHARPNESS,
            min_difference: float = VIDEO_MIN_DIFFERENCE,
            sample_interval: float = VIDEO_SAMPLE_INTERVAL,
        ):
        self.video_path = video_path
        self.output_dir = output_dir
        self.min_sharpness = min_sharpness
        self.min_difference = min_difference
        self.sample_interval = sample_interval

        self._run_constructor_validator()

    def _run_constructor_validator(self):
        if not self.video_path.exists():
            raise VideoExtractorError(f'Video file not found: {self.video_path}')
        
        if self.video_path.suffix.lower() not in SUPPORTED_VIDEO_FORMATS:
            raise VideoExtractorError(f'Unsupported video format: {self.video_path.suffix}.')
        
        cap = cv2.VideoCapture(str(self.video_path))
        if not cap.isOpened():
            cap.release()
            raise VideoExtractorError(f'Cannot open video: {self.video_path}')
        
        self._fps = cap.get(cv2.CAP_PROP_FPS)
        self._total_frames = int(cap.get(cv2.CAP_PROP_FRAME_COUNT))
        self._width = int(cap.get(cv2.CAP_PROP_FRAME_WIDTH))
        self._height = int(cap.get(cv2.CAP_PROP_FRAME_HEIGHT))
        self._duration = self._total_frames / self._fps if self._fps > 0 else 0
        cap.release()

        if self._fps <= 0 or self._total_frames <= 0:
            raise VideoExtractorError('Invalid video: cannot read FPS or frame count.')
        
        if self._duration < 5:
            raise VideoExtractorError('Video too short: minimum 5 seconds required.')
        
        success_alert(f'Video extracotr manager started.')

    def start_captured_images_extraction(self) -> None:
        """
        Funzione per generare le foto da un video.
        """
        self.output_dir.mkdir(parents=True, exist_ok=True)

        valid_frames: list[Path] = []
        last_accepted: numpy.ndarray = None

        frame_interval = max(1, int(self._fps * self.sample_interval))
        total_samples = (self._total_frames + frame_interval - 1) // frame_interval
        iterable_progress_bar =  progress_bar(self._run_frames_exractor(), description='Images extracting from video')
        iterable_progress_bar.total = total_samples

        index = 0
        errors = 0

        for frame in iterable_progress_bar:
            try:
                self._frame_validation(frame, last_accepted)
                frame_path = self._save_frame(frame, index)
                last_accepted = frame
                valid_frames.append(frame_path)
                index += 1
            except Exception:
                errors += 1

        self.valid_frames = valid_frames

        if errors > 0: warning_alert(f'{errors} frames discarded.')

        if len(valid_frames) <= DEFAULT_MIN_PHOTO_ERROR: raise VideoExtractorError('Insufficient frames detected.')

        if len(valid_frames) <= DEFAULT_MIN_PHOTO_WARNING: warning_alert(f'Less than {DEFAULT_MIN_PHOTO_WARNING} frames detected.')

        success_alert('Video extraction completed.')

    def _frame_validation(self, frame: numpy.ndarray, last_accepted: numpy.ndarray) -> None:
        """
        Funzione che gestisce i filtri sulle immagini.
        """
        self._run_blurry_frames_remover(frame)

        if last_accepted is not None: self._run_redundant_frames_remover(frame, last_accepted)

    def _run_frames_exractor(self):
        """
        Funzione che genera il flusso di frame.
        """
        cap = cv2.VideoCapture(str(self.video_path))
        count = 0
        frame_interval = max(1, int(self._fps * self.sample_interval))

        while cap.isOpened():
            ret, frame = cap.read()
            if not ret:
                break
            
            if count % frame_interval == 0:
                yield frame 
                
            count += 1
        cap.release()
    
    def _run_blurry_frames_remover(self, frame: numpy.ndarray) -> None:
        """
        Funzione che filtra i frame che sono troppo mossi
        """
        gray = cv2.cvtColor(frame, cv2.COLOR_BGR2GRAY)

        h, w = gray.shape
        if w > 1024:
            scale = 1024 / w
            gray = cv2.resize(gray, None, fx=scale, fy=scale)

        laplacian_var = cv2.Laplacian(gray, cv2.CV_64F).var()

        if laplacian_var < self.min_sharpness:
            raise VideoExtractorError('Frame discarded')
            

    def _run_redundant_frames_remover(self, frame: numpy.ndarray, last_accepted: numpy.ndarray) -> None:
        """
        Funzione che filtra i frame troppo uguali
        """
        gray_current = cv2.cvtColor(frame, cv2.COLOR_BGR2GRAY)
        gray_last = cv2.cvtColor(last_accepted, cv2.COLOR_BGR2GRAY)

        scale = 0.5
        gray_current = cv2.resize(gray_current, None, fx=scale, fy=scale)
        gray_last = cv2.resize(gray_last, None, fx=scale, fy=scale)

        result = cv2.matchTemplate(gray_current, gray_last, cv2.TM_CCOEFF_NORMED)
        _, max_val, _, _ = cv2.minMaxLoc(result)
        
        if max_val > (1.0 - self.min_difference):
            raise Exception('Frame discarded')

    def _save_frame(self, frame: numpy.ndarray, image_index: int) -> Path:
        """
        Funzione per salvare l'immagine filtrata.
        """
        image_name = f'image_{image_index:04d}.jpg'
        image_path = self.output_dir / image_name

        success = cv2.imwrite(
            str(image_path), 
            frame, 
            [cv2.IMWRITE_JPEG_QUALITY, 95]
        )

        if not success:
            raise VideoExtractorError(f'Failed to save image: {image_path}')
        
        return image_path