CLR_RESET = "\033[0m"     # Bianco
CLR_WARNING = "\033[93m"  # Giallo
CLR_ERROR = "\033[91m"    # Rosso

class BaseError(Exception):
    """Classe base per tutti gli errori custom del progetto."""
    def __init__(self, message: str, suggestion: str = None, error_type: str = CLR_ERROR):
        self.message = message
        self.suggestion = suggestion
        self.error_type = error_type
        super().__init__(self.message)

    def __str__(self):
        error_name = self.__class__.__name__
        text = f"\n[ERROR] {error_name}: {self.message}"
        if self.suggestion:
            text += f"\n[SUGGESTION] -> {self.suggestion}"
        return f'{self.error_type}{text}{CLR_RESET}'

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

class MetadataExtractionError(BaseError):
    """Sollevata quando l'immagine si apre, ma i dati EXIF sono corrotti o malformati."""
    def __init__(self, image_path: str, detail: str = ''):
        message = f"Failed to parse EXIF metadata in: '{image_path}'"
        suggestion = f"Check image metadata format. Detail: {detail}"
        super().__init__(message, suggestion, CLR_WARNING)

class EmptyDatasetError(BaseError):
    """Sollevata quando una lista (es. le immagini estratte) è completamente vuota."""
    def __init__(self, step_name: str = "Processing"):
        message = f"No valid data available after the phase: {step_name}."
        suggestion = "Check that the data is not corrupted and is located in the correct folder."
        super().__init__(message, suggestion, CLR_ERROR)