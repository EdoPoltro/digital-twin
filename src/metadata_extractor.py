from models.image_data import CapturedImage
from PIL import Image, UnidentifiedImageError
from PIL.ExifTags import TAGS
from utils.exceptions import ImageLoadError, MetadataExtractionError

EXIF_OFFSET_ID = 0x8769

def extract_raw_captured_image_metadata(raw_captured_image: CapturedImage) -> None: 
    """
    Funzione che gestisce funzione che recupera i metadati di un immagine.

    Attributes:
        raw_captured_image (CapturedImage): istanza di un immagine

    Returns:
        None

    Raises:
        ImageLoadError: se c'è stato un errore nell'apertura dell'immagine
        MetadataExtractionError: se i metadati sono corrotti o sono spazzatura
    """
    try:
        with Image.open(raw_captured_image.file_path) as opend_image:
            raw_captured_image.camera_metadata.resolution = opend_image.size
            exif_data = opend_image.getexif()

            if not exif_data: return
            if not EXIF_OFFSET_ID in exif_data: return

            extended_exif_data = opend_image.getexif().get_ifd(EXIF_OFFSET_ID)

            extended_exif_data= {TAGS.get(tag_id, tag_id): value for tag_id, value in extended_exif_data.items()}
            exif_data = {**{TAGS.get(t, t): v for t, v in exif_data.items()}, **extended_exif_data}

    except (UnidentifiedImageError, OSError) as e:
        raise ImageLoadError(raw_captured_image.file_path)
    
    try:
        if "Make" in exif_data:
            raw_captured_image.camera_metadata.make = str(exif_data["Make"]).strip()
        if "Model" in exif_data:
            raw_captured_image.camera_metadata.model = str(exif_data["Model"]).strip()
        if "FocalLength" in exif_data:
            raw_captured_image.camera_metadata.focal_length = float(exif_data["FocalLength"])

        # TODO: Più avanti aggiungeremo qui la lettura del GPS per spatial_metadata

    except (ValueError, TypeError) as e:
        raise MetadataExtractionError(raw_captured_image.file_path, str(e))

def extract_all_raw_captured_images_metadata(raw_captured_images: list[CapturedImage]) -> None:
    """
    Funzione che gestisce il ciclo for per estrarre i metadati di tutte le immagini.

    Attributes:
        raw_captured_images (list[CapturedImage]): lista di istanze delle immagini

    Returns:
        None

    Raises:
        ImageLoadError: se c'è stato un errore nell'apertura dell'immagine
        MetadataExtractionError: se i metadati sono corrotti o sono spazzatura
    """
    for raw_captured_image in raw_captured_images:
        extract_raw_captured_image_metadata(raw_captured_image)
