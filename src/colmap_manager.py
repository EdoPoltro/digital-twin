
from pathlib import Path
from models.image_data import CameraMetadata, CapturedImage, SpatialMetadata

def upload_captured_image_camera_data(camera_metadata: CameraMetadata, file_name: str):
    pass

def upload_captured_image_gps_data(spatial_metadata: SpatialMetadata, file_name: str):
    pass

def upload_captured_image_metadata(captured_image: CapturedImage):
    """
    Funzione che gestisce la scrittura dei metadati di una immagine già processata per
    usarla in colmap.

    Args:
        captured_images (CapturedImage): immagine da caricare

    Raises:
    """
    upload_captured_image_camera_data(captured_image.camera_metadata, captured_image.file_name)
    upload_captured_image_gps_data(captured_image.spatial_metadata, captured_image.file_name)

def upload_captured_images_metadata(captured_images: list[CapturedImage]):
    """
    Funzione che gestisce la scrittura dei metadati di una lista di immagini già processate per
    usarle in colmap.

    Args:
        captured_images (list[CapturedImage]): lista di immagini da caricare

    Raises:
    """
    for captured_image in captured_images:
        try:
            upload_captured_images_metadata(captured_image)
        except Exception as e: # da rendere piu rigoroso
            print(e)
