from typing import Literal

from config import DEFAULT_IMAGES_EXTRACTION_MODE, DEFAULT_SCAN_MODE
from src.colmap.colmap_manager import ColmapManager
from src.colmap.metadata_uploader import start_full_metadata_uploading
from src.models.captured_image import CapturedImage, ImageStatus
from src.open3d.open3d_manager import Open3dManager
from src.openmvs.openmvs_manager import OpenmvsManager
from src.processing.ingestion import get_raw_captured_images
from src.processing.metadata_extractor import extract_all_raw_captured_images_metadata
from src.processing.processor_manager import ProcessorManager
from src.core.exceptions import BaseError
from src.processing.video_extractor_manager import VideoExtractorManager
from src.utils.io_utils import setup_project_environment

def start_digital_twin_pipeline(extraction_mode: Literal['video', 'images'] = DEFAULT_IMAGES_EXTRACTION_MODE, scan_mode: Literal['indoor', 'outdoor'] = DEFAULT_SCAN_MODE):
    try:
        print("="*80)
        print(f'Digital Twin 3D - Avvio pipline - {DEFAULT_SCAN_MODE.capitalize()} mode')
        print("="*80)

        open3d = Open3dManager()

        # open3d.start_full_open3d_pipeline()

        open3d.run_mesh_importer()

        open3d.run_viewer()

        return

        setup_project_environment()

        if extraction_mode == 'video': 

            video = VideoExtractorManager()

            video.start_captured_images_extraction()

        captured_images: list[CapturedImage] = get_raw_captured_images()
        
        if extraction_mode == 'images': captured_images = extract_all_raw_captured_images_metadata(captured_images)

        processor = ProcessorManager(captured_images)

        processor.start_full_processing()

        captured_images = processor.get_captured_images()

        if scan_mode == 'outdoor' and extraction_mode == 'images': start_full_metadata_uploading(captured_images)

        colmap = ColmapManager(use_gpu=True)

        colmap.start_full_colmap_pipeline()

        openmvs = OpenmvsManager()

        openmvs.start_full_openmvs_pipeline() 

        open3d = Open3dManager()

        open3d.start_full_open3d_pipeline()

        print("="*80)
        print(f'Digital Twin 3D - pipeline terminata')
        print("="*80)
    except BaseError as e:
        print(e)
    except Exception as e:
        print(f'Errore critico di sistema: {e}')

