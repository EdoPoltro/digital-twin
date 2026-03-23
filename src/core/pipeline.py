from config import DATA_COLMAP_DIR, DEFAULT_ENVIRONMENT_CLEAN_UP, DEFAULT_SCAN_MODE, DEFAULT_SYSTEM_MODE
from src.colmap.colmap_manager import ColmapManager
from src.colmap.metadata_uploader import start_full_metadata_uploading
from src.models.captured_image import CapturedImage, ImageStatus
from src.open3d.open3d_manager import Open3dManager
from src.openmvs.openmvs_manager import OpenmvsManager
from src.processing.ingestion import get_raw_captured_images
from src.processing.metadata_extractor import extract_all_raw_captured_images_metadata
from src.processing.promoter import promote_captured_images
from src.core.exceptions import BaseError
from src.utils.io_utils import setup_project_environment
from src.utils.log_utils import success_alert

def start_digital_twin_pipeline():
    try:
        print("="*80)
        print(f'Digital Twin 3D - Avvio pipline - {DEFAULT_SCAN_MODE.capitalize()} mode')
        print("="*80)

        open3d = Open3dManager()

        open3d.start_full_open3d_pipeline(4,2)

        # open3d.import_from_openmvs()

        # open3d.generate_resized_mesh(4,2)

        # open3d.run_noise_remover()

        # open3d.run_mesh_exporter()

        # open3d.run_visualizer()

        return

        setup_project_environment(DEFAULT_ENVIRONMENT_CLEAN_UP)

        # aggiungere in input la cartella
        captured_images: list[CapturedImage] = get_raw_captured_images()
        
        captured_images = extract_all_raw_captured_images_metadata(captured_images)

        # da rivedere quando aggiungo i filtri alle immagini
        captured_images = promote_captured_images(captured_images, ImageStatus.PROCESSED)

        # success_alert('Upload dei metadati.')
        start_full_metadata_uploading(captured_images)

        colmap = ColmapManager()

        colmap.generate_sparse_point_cloud()
        # colmap.generate_sparse_point_cloud(use_gpu=True) pc nvidia

        colmap.generate_undistort_images()

        # colmap.start_full_colmap_pipeline()

        # colmap.run_poisson_mesher()

        openmvs = OpenmvsManager()

        openmvs.import_from_colmap()

        openmvs.generate_dense_point_cloud()

        # openmvs.reconstruct_mesh()

        # openmvs.texture_mesh_from_colmap()
        
    except BaseError as e:
        print(e)
    except Exception as e:
        print(f'Errore critico di sistema: {e}')

