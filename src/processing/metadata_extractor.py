from typing import Any, Literal
from config import DEFAULT_MIN_PHOTO_ERROR, DEFAULT_MIN_PHOTO_WARNING, DEFAULT_SCAN_MODE
from src.models.captured_image import CapturedImage, ImageStatus
from PIL import Image
from PIL.ExifTags import TAGS, GPSTAGS, IFD
from src.core.exceptions import MetadataExtractorError
from src.processing.promoter import remove_error_images
from src.utils.log_utils import success_alert, warning_alert
from src.utils.math_utils import exif_gps_to_decimal
from datetime import datetime

def _extract_camera_metadata(raw_captured_image: CapturedImage, exif_data: dict[str | int, Any]) -> None:
    """
    Funzione che gestisce funzione che recupera i metadati della camera di un immagine.

    Args:
        raw_captured_image (CapturedImage): istanza di un immagine
        exif_data (dict[str | int, Any]): dati exif
        
    Raises:
        MetadataExtractorError
    """
    if not IFD.Exif in exif_data: raise MetadataExtractorError('No cmaera information available.')
    
    extended_exif_data = exif_data.get_ifd(IFD.Exif)
    extended_exif_data= {TAGS.get(tag_id, tag_id): value for tag_id, value in extended_exif_data.items()}
    camera_data = {**{TAGS.get(t, t): v for t, v in exif_data.items()}, **extended_exif_data}

    if "Make" in camera_data:
        raw_captured_image.camera_metadata.make = str(camera_data["Make"]).strip()
    if "Model" in camera_data:
        raw_captured_image.camera_metadata.model = str(camera_data["Model"]).strip()
    if "FocalLength" in camera_data:
        raw_captured_image.camera_metadata.focal_length = float(camera_data["FocalLength"])
    else:
        raise MetadataExtractorError('No focal length available.')
    if "DateTimeOriginal" in camera_data: 
        try:
            date_str = str(camera_data["DateTimeOriginal"]).strip()
            raw_captured_image.spatial_metadata.timestamp = datetime.strptime(date_str, "%Y:%m:%d %H:%M:%S")
        except Exception:
            pass
    if "FocalLengthIn35mmFilm" in camera_data:
        focal_35mm = camera_data.get("FocalLengthIn35mmFilm")
    else:
        raise MetadataExtractorError('No focal length 35mm available.')

    crop_factor = float(focal_35mm) / float(raw_captured_image.camera_metadata.focal_length)
    sensor_w = round(36.0 / crop_factor, 2)
    sensor_h = round(24.0 / crop_factor, 2)
    raw_captured_image.camera_metadata.sensor_size = (sensor_w, sensor_h)
            
def _extract_gps_metadata(raw_captured_image: CapturedImage, exif_data: dict[str | int, Any]) -> None:
    """
    Funzione che gestisce funzione che recupera i metadati del gps di un immagine.

    Args:
        raw_captured_image (CapturedImage): istanza di un immagine
        exif_data (dict[str | int, Any]): dati exif

    Raises:
        MetadataExtractorError
    """
    if not IFD.GPSInfo in exif_data: raise MetadataExtractorError("No GPS information available.")

    spatial_exif = exif_data.get_ifd(IFD.GPSInfo)
    spatial_exif = {GPSTAGS.get(tag, tag): value for tag, value in spatial_exif.items()}

    if 'GPSLatitude' in spatial_exif:
        latitude = exif_gps_to_decimal(spatial_exif['GPSLatitude'])
        if spatial_exif.get('GPSLatitudeRef', 'N') == 'S':
            latitude = -latitude
        raw_captured_image.spatial_metadata.latitude = latitude
    else:
        raise MetadataExtractorError("Latitude missing from GPS data.")
    
    if 'GPSLongitude' in spatial_exif:
        longitude = exif_gps_to_decimal(spatial_exif['GPSLongitude'])
        if spatial_exif.get('GPSLongitudeRef', 'E') == 'W': 
            longitude = -longitude
        raw_captured_image.spatial_metadata.longitude = longitude
    else:
        raise MetadataExtractorError("Longitude missing from GPS data.")

    if 'GPSAltitude' in spatial_exif:
        altitude = float(spatial_exif['GPSAltitude'])
        if spatial_exif.get('GPSAltitudeRef', 0) == 1:
            altitude = -altitude
        raw_captured_image.spatial_metadata.altitude = altitude
    else:
        raise MetadataExtractorError("Altitude missing from GPS data.")
        
def extract_raw_captured_image_metadata(raw_captured_image: CapturedImage, scan_mode: Literal['indoor', 'outdoor'] = DEFAULT_SCAN_MODE) -> None: 
    """
    Funzione che gestisce funzione che recupera i metadati di un immagine.

    Args:
        raw_captured_image (CapturedImage): istanza di un immagine

    Returns:
        None

    Raises:
        MetadataExtractorError
    """
    with Image.open(raw_captured_image.file_path) as opend_image:
        resolution = opend_image.size 
        if not resolution: raise MetadataExtractorError("No resolution found")
        raw_captured_image.camera_metadata.resolution = resolution

        exif_data = opend_image.getexif()
        if not exif_data: raise MetadataExtractorError("No EXIF data found")

        _extract_camera_metadata(raw_captured_image, exif_data)

        try:
            _extract_gps_metadata(raw_captured_image, exif_data)
        except Exception as e: 
            if scan_mode == 'indoor':
                pass
            elif scan_mode == 'outdoor':
                raise MetadataExtractorError(e)

def extract_all_raw_captured_images_metadata(raw_captured_images: list[CapturedImage], scan_mode: Literal['indoor', 'outdoor'] = DEFAULT_SCAN_MODE) -> list[CapturedImage]:
    """
    Funzione che gestisce il ciclo for per estrarre i metadati di tutte le immagini.
    In caso venga lanciata una eccezione da un'immagine allora lo stato dell'immagine viene messo ad ERROR.

    Args:
        raw_captured_images (list[CapturedImage]): lista di istanze delle immagini

    Raise:
        MetadataExtractorError: quando la lista è vuota
    """
    errors = 0

    for raw_captured_image in raw_captured_images:
        try:
            extract_raw_captured_image_metadata(raw_captured_image, scan_mode)
        except Exception as e:
            raw_captured_image.status = ImageStatus.ERROR
            errors += 1
            warning_alert(f'Metadata extraction failed for photo {raw_captured_image.file_name}, {e}.')

    output_raw_captured_images = remove_error_images(raw_captured_images)

    if errors > 0: warning_alert(f'{errors} photos removed.')

    if len(output_raw_captured_images) <= DEFAULT_MIN_PHOTO_ERROR: raise MetadataExtractorError('Insufficient photos detected.')

    if len(output_raw_captured_images) <= DEFAULT_MIN_PHOTO_WARNING: warning_alert(f'Less than {DEFAULT_MIN_PHOTO_WARNING} images detected in the project folder.')

    success_alert('Metadata extraction completed.')

    return output_raw_captured_images
