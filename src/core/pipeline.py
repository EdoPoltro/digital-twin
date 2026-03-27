from config import DATA_OPEN3D_DIR, DATA_OPENMVS_DENSE_MVS, DATA_OPENMVS_ALIGNED_MVS_MESH_MVS, DATA_OPENMVS_ALIGNED_MVS_MESH_PLY, DEFAULT_SCAN_MODE
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

        setup_project_environment()

        captured_images: list[CapturedImage] = get_raw_captured_images()
        
        captured_images = extract_all_raw_captured_images_metadata(captured_images)

        processor = ProcessorManager(captured_images)

        processor.start_full_processing()

        captured_images = processor.get_captured_images()

        if DEFAULT_SCAN_MODE == 'outdoor': start_full_metadata_uploading(captured_images)

        colmap = ColmapManager(output_log=True) # output log per test

        colmap.start_full_colmap_pipeline(use_gpu=False)

        openmvs = OpenmvsManager(output_log=True) # output log per test

        openmvs.start_full_openmvs_pipeline() 

        open3d = Open3dManager()

        open3d.start_full_open3d_pipeline()
        
    except BaseError as e:
        print(e)
    except Exception as e:
        print(f'Errore critico di sistema: {e}')

