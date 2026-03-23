from config import DEFAULT_ENVIRONMENT_CLEAN_UP, DEFAULT_SCAN_MODE
from src.colmap.colmap_manager import ColmapManager
from src.colmap.metadata_uploader import start_full_metadata_uploading
from src.models.captured_image import CapturedImage, ImageStatus
from src.open3d.open3d_manager import Open3dManager
from src.openmvs.openmvs_manager import OpenmvsManager
from src.processing.ingestion import get_raw_captured_images
from src.processing.metadata_extractor import extract_all_raw_captured_images_metadata
from src.processing.processor_manager import ProcessorManager
from src.processing.promoter import promote_captured_images
from src.core.exceptions import BaseError
from src.utils.io_utils import setup_project_environment

def start_digital_twin_pipeline():
    try:
        print("="*80)
        print(f'Digital Twin 3D - Avvio pipline - {DEFAULT_SCAN_MODE.capitalize()} mode')
        print("="*80)

        setup_project_environment(DEFAULT_ENVIRONMENT_CLEAN_UP)

        # aggiungere in input la cartella
        captured_images: list[CapturedImage] = get_raw_captured_images()
        
        captured_images = extract_all_raw_captured_images_metadata(captured_images)

        processor = ProcessorManager(captured_images)

        processor.start_full_processing()

        captured_images = processor.get_captured_images()

        start_full_metadata_uploading(captured_images)

        colmap = ColmapManager()

        colmap.start_full_colmap_pipeline(use_gpu=False)

        return

        # colmap.generate_sparse_point_cloud()

        # colmap.generate_aligned_point_cloud()

        # colmap.generate_undistort_images()

        openmvs = OpenmvsManager()

        openmvs.import_from_colmap()

        openmvs.generate_dense_point_cloud()

        # openmvs.reconstruct_mesh()

        # openmvs.texture_mesh_from_colmap()

        open3d = Open3dManager()

        open3d.start_full_open3d_pipeline() # da mettere i valori di scala in indoor

        # open3d.import_from_openmvs()

        # open3d.generate_resized_mesh()

        # open3d.run_noise_remover()

        # open3d.run_mesh_exporter()

        # open3d.run_visualizer()
        
    except BaseError as e:
        print(e)
    except Exception as e:
        print(f'Errore critico di sistema: {e}')

