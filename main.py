from config import DATA_COLMAP_ALIGNED_DIR, DATA_COLMAP_SPARSE_DIR, DEFAULT_ENVIRONMENT_CLEAN_UP
from src.models.captured_image import CapturedImage, ImageStatus
from src.colmap.colmap_manager import ColmapManager
from src.colmap.metadata_uploader import start_full_metadata_uploading
from src.processing.ingestion import get_raw_captured_images
from src.processing.metadata_extractor import extract_all_raw_captured_images_metadata
from src.processing.promoter import promote_captured_images
from src.core.exceptions import BaseError
from src.utils.helpers_io import setup_project_environment
from src.utils.logging_utils import log_alert

def main():
    print("="*40)
    print('Digital Twin 3D - Avvio pipline')
    print("="*40)

    try:
        log_alert("Setup in corso.")
        setup_project_environment(DEFAULT_ENVIRONMENT_CLEAN_UP)

        log_alert("Creazione dell\'array di immagini.")
        captured_images: list[CapturedImage] = get_raw_captured_images()

        log_alert('Estrazione dei metadati.')
        extract_all_raw_captured_images_metadata(captured_images)

        log_alert('Avvio promoter.')
        promote_captured_images(captured_images, ImageStatus.PROCESSED)

        log_alert('Pulizia Array di immagini.')
        captured_images = list(filter(lambda img: img.status is not ImageStatus.ERROR, captured_images))

        log_alert('Upload dei metadati.')
        start_full_metadata_uploading(captured_images)

        log_alert('Inizializzazione di colmap.exe.')
        colmap = ColmapManager()

        # colmap._run_model_aligner(DATA_COLMAP_ALIGNED_DIR, DATA_COLMAP_SPARSE_DIR)

        
    except BaseError as e:
        print(e)
    except Exception as e:
        print(f'Errore critico di sistema: {e}')

if __name__ == "__main__":
    main()