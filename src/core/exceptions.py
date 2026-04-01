from src.utils.log_utils import CLR_ERROR, CLR_RESET, CLR_WARNING

class BaseError(Exception):
    """Classe base per tutti gli errori custom del progetto."""
    def __init__(self, exception_message: str, exception_suggestion: str = None, exception_type: str = CLR_ERROR):
        self.exception_message = exception_message
        self.exception_suggestion = exception_suggestion
        self.exception_type = exception_type
        super().__init__(self.exception_message)

    def __str__(self):
        exception_name = self.__class__.__name__
        if self.exception_type == CLR_ERROR:
            text = f"\n[ERROR] {exception_name}: {self.exception_message}"
        else:
            text = f"\n[WARNING] {exception_name}: {self.exception_message}"
        if self.exception_suggestion:
            text += f"\n[SUGGESTION] -> {self.exception_suggestion}"
        return f'{self.exception_type}{text}{CLR_RESET}'

class EnvSetupError(BaseError):
    def __init__(self, exception_message: str, exception_type: str = CLR_ERROR):
        suggestion = "Check function setup_project_environment() in io_utils.pys."
        super().__init__(exception_message, suggestion, exception_type)

class VideoExtractorError(BaseError):
    def __init__(self, exception_message: str, exception_type: str = CLR_ERROR):
        suggestion = "Check file video_extractor_manager.py."
        super().__init__(exception_message, suggestion, exception_type)

class UtilsError(BaseError):
    def __init__(self, exception_message: str, exception_type: str = CLR_ERROR):
        suggestion = "Check utils functions."
        super().__init__(exception_message, suggestion, exception_type)

class IngestionError(BaseError):
        def __init__(self, exception_message: str, exception_type: str = CLR_ERROR):
            suggestion = "Check file ingestion.py."
            super().__init__(exception_message, suggestion, exception_type)

class MetadataExtractorError(BaseError):
    def __init__(self, exception_message: str, exception_type: str = CLR_ERROR):
        suggestion = "Check file metadata_extractor.py."
        super().__init__(exception_message, suggestion, exception_type)
        
class ProcessorError(BaseError):
    def __init__(self, exception_message: str, exception_type: str = CLR_ERROR):
        suggestion = "Check file processor_manager.py."
        super().__init__(exception_message, suggestion, exception_type)

class PromoterError(BaseError):
    def __init__(self, exception_message: str, exception_type: str = CLR_ERROR):
        suggestion = "Check file promoter.py."
        super().__init__(exception_message, suggestion, exception_type)

class MetadataUploaderError(BaseError):
    def __init__(self, exception_message: str, exception_type: str = CLR_ERROR):
        exception_suggestion = "Check file metadata_uploader.py."
        super().__init__(exception_message, exception_suggestion, exception_type)

class ColmapError(BaseError):
    def __init__(self, exception_message: str, exception_type: str = CLR_ERROR):
        exception_suggestion = "Check file colmap_manager.py."
        super().__init__(exception_message, exception_suggestion, exception_type)

class OpenmvsError(BaseError):
    def __init__(self, exception_message: str, exception_type: str = CLR_ERROR):
        exception_suggestion = "Check file openmvs_manager.py."
        super().__init__(exception_message, exception_suggestion, exception_type)

class Open3dError(BaseError):
    def __init__(self, exception_message: str, exception_type: str = CLR_ERROR):
        exception_suggestion = "Check file open3d_manager.py."
        super().__init__(exception_message, exception_suggestion, exception_type)
