from typing import Any
from models.image_data import CapturedImage
from PIL import Image, UnidentifiedImageError
from PIL.ExifTags import TAGS, GPSTAGS, IFD
from utils.exceptions import BaseError, ImageLoadError, MetadataExtractionError, EmptyDatasetError
from utils.math_utils import exif_gps_to_decimal
from datetime import datetime

def extract_camera_metadata(raw_captured_image: CapturedImage, exif_data: dict[str | int, Any]) -> None:
    """
    Funzione che gestisce funzione che recupera i metadati della camera di un immagine.

    Args:
        raw_captured_image (CapturedImage): istanza di un immagine
        exif_data (dict[str | int, Any]): dati exif
        
    Returns:
        None
    """
    if IFD.Exif in exif_data: 
        extended_exif_data = exif_data.get_ifd(IFD.Exif)
        extended_exif_data= {TAGS.get(tag_id, tag_id): value for tag_id, value in extended_exif_data.items()}
        camera_data = {**{TAGS.get(t, t): v for t, v in exif_data.items()}, **extended_exif_data}
    else:
        camera_data = {TAGS.get(t, t): v for t, v in exif_data.items()}
    
    if "Make" in camera_data:
        raw_captured_image.camera_metadata.make = str(camera_data["Make"]).strip()
    if "Model" in camera_data:
        raw_captured_image.camera_metadata.model = str(camera_data["Model"]).strip()
    if "FocalLength" in camera_data:
        raw_captured_image.camera_metadata.focal_length = float(camera_data["FocalLength"])
    if "DateTimeOriginal" in camera_data: 
        date_str = str(camera_data["DateTimeOriginal"]).strip()
        try:
            raw_captured_image.spatial_metadata.timestamp = datetime.strptime(date_str, "%Y:%m:%d %H:%M:%S")
        except ValueError:
            pass
    
    focal_35mm = camera_data.get("FocalLengthIn35mmFilm")
    focal = camera_data.get("FocalLength")

    if focal_35mm and focal:
        try:
            crop_factor = float(focal_35mm) / float(focal)
        
            sensor_w = round(36.0 / crop_factor, 2)
            sensor_h = round(24.0 / crop_factor, 2)

            raw_captured_image.camera_metadata.sensor_size = (sensor_w, sensor_h)
        except ZeroDivisionError:
            pass
            
def extract_gps_metadata(raw_captured_image: CapturedImage, exif_data: dict[str | int, Any]) -> None:
    """
    Funzione che gestisce funzione che recupera i metadati del gps di un immagine.

    Args:
        raw_captured_image (CapturedImage): istanza di un immagine
        exif_data (dict[str | int, Any]): dati exif
        
    Returns:
        None
    """
    if not IFD.GPSInfo in exif_data: raise MetadataExtractionError(raw_captured_image.file_path, "No GPS information available.")

    spatial_exif = exif_data.get_ifd(IFD.GPSInfo)
    spatial_exif = {GPSTAGS.get(tag, tag): value for tag, value in spatial_exif.items()}

    if 'GPSLatitude' not in spatial_exif or 'GPSLongitude' not in spatial_exif:
        raise MetadataExtractionError(raw_captured_image.file_path, "Latitude or Longitude coordinates missing from GPS data.")
    
    latitude = exif_gps_to_decimal(spatial_exif['GPSLatitude'])
    if spatial_exif.get('GPSLatitudeRef', 'N') == 'S':
        latitude = -latitude
    raw_captured_image.spatial_metadata.latitude = latitude

    longitude = exif_gps_to_decimal(spatial_exif['GPSLongitude'])
    if spatial_exif.get('GPSLongitudeRef', 'E') == 'W':
        longitude = -longitude
    raw_captured_image.spatial_metadata.longitude = longitude

    if 'GPSAltitude' in spatial_exif:
        altitude = float(spatial_exif['GPSAltitude'])
        if spatial_exif.get('GPSAltitudeRef', 0) == 1:
            altitude = -altitude
        raw_captured_image.spatial_metadata.altitude = altitude
        
def extract_raw_captured_image_metadata(raw_captured_image: CapturedImage) -> None: 
    """
    Funzione che gestisce funzione che recupera i metadati di un immagine.

    Args:
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

            if not exif_data: raise MetadataExtractionError(raw_captured_image.file_path, "No EXIF data found")

            extract_camera_metadata(raw_captured_image, exif_data)
            extract_gps_metadata(raw_captured_image, exif_data)
    except (UnidentifiedImageError, OSError) as e:
        raise ImageLoadError(raw_captured_image.file_path)
    except (ValueError, TypeError, IndexError) as e:
        raise MetadataExtractionError(raw_captured_image.file_path, str(e))

def extract_all_raw_captured_images_metadata(raw_captured_images: list[CapturedImage]) -> list[CapturedImage]:
    """
    Funzione che gestisce il ciclo for per estrarre i metadati di tutte le immagini.
    In caso venga lanciata una eccezione da un'immagine allora l'immagine viene scartata dalla lista.

    Args:
        raw_captured_images (list[CapturedImage]): lista di istanze delle immagini

    Returns:
        list[CapturedImage]

    Raise:
        EmptyDatasetError: quando la lista è vuota
    """
    raw_captured_images_verified: list[CapturedImage] = []
    for raw_captured_image in raw_captured_images:
        try:
            extract_raw_captured_image_metadata(raw_captured_image)
            raw_captured_images_verified.append(raw_captured_image)
        except BaseError as e:
            print(e)

    if len(raw_captured_images_verified) == 0: raise EmptyDatasetError(step_name="EXIF Metadata Extraction")

    return raw_captured_images_verified
