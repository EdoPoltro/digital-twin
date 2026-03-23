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

class FolderNotFoundError(BaseError):
    """Sollevata quando una cartella specifica non viene trovata."""
    def __init__(self, folder_path: str):
        message = f"Folder not found: '{folder_path}'"
        suggestion = "Check if the folder exists and the path is correct."
        super().__init__(message, suggestion, CLR_ERROR)

class FolderAccessError(BaseError):
    """Sollevata per permessi negati."""
    def __init__(self, folder_path: str):
        message = f"Access denied: '{folder_path}'"
        suggestion = "Check OS permissions (Read/Execute)."
        super().__init__(message, suggestion, CLR_ERROR)

class FileAccessError(BaseError):
    """Sollevata per permessi negati."""
    def __init__(self, file_path: str):
        message = f"Access denied: '{file_path}'"
        suggestion = "Check OS permissions (Read/Execute)."
        super().__init__(message, suggestion, CLR_ERROR)

class FileNotFoundError(BaseError):
    """Sollevata quando un file specifico (es. un'immagine) non viene trovato."""
    def __init__(self, file_path: str):
        message = f"File not found: '{file_path}'"
        suggestion = "Check if the file exists and the path is correct."
        super().__init__(message, suggestion, CLR_ERROR)

class ImageLoadError(BaseError):
    def __init__(self, image_path: str):
        message = f"Image load error: '{image_path}'"
        suggestion = "Check if the image is corrupted."
        super().__init__(message, suggestion, CLR_WARNING)

class EmptyDatasetError(BaseError):
    """Sollevata quando una lista (es. le immagini estratte) è completamente vuota."""
    def __init__(self, step_name: str = "Processing"):
        message = f"No valid data available after the phase: {step_name}."
        suggestion = "Check that the data is not corrupted and is located in the correct folder."
        super().__init__(message, suggestion, CLR_ERROR)

class ImageCopyError(BaseError):
    def __init__(self, image_path: str):
        message = f"Image copy error: '{image_path}'"
        suggestion = "Check if the image exists."
        super().__init__(message, suggestion, CLR_WARNING)




        
class EnvSetupError(BaseError):
    def __init__(self, exception_message: str, exception_type: str = CLR_ERROR):
        suggestion = "Check function setup_project_environment() in io_utils.pys."
        super().__init__(exception_message, suggestion, exception_type)

class IngestionError(BaseError):
        def __init__(self, exception_message: str, exception_type: str = CLR_ERROR):
            suggestion = "Check file ingestion.py."
            super().__init__(exception_message, suggestion, exception_type)

class MetadataExtractorError(BaseError):
    def __init__(self, exception_message: str, exception_type: str = CLR_ERROR):
        suggestion = "Check file metadata_extractor.py."
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
