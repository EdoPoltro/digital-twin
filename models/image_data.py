from dataclasses import dataclass, field
from enum import Enum, auto
from typing import Optional, Dict
import datetime
import os
import uuid

class ImageStatus(Enum):
    """Definisce gli stati possibili di un'immagine nella pipeline."""
    RAW = auto()          
    PROCESSED = auto()    
    RECONSTRUCTED = auto() 
    ERROR = auto()   

@dataclass
class CameraMetadata:
    """
    Parametri relativi all'ottica e al sensore.

    Attributes:
        make (str): marca della fotocamera 
        model (str): modello della fotocamera
        focal_length (float): lunghezza focale dell'obbiettivo
        sensor_size (tuple): dimensore del sensore
        resolution (tuple): risoluzione scatto
    """
    make: Optional[str] = None
    model: Optional[str] = None
    focal_length: Optional[float] = None
    sensor_size: Optional[tuple] = None
    resolution: tuple = (0, 0)

@dataclass
class SpatialMetadata:
    """
    Parametri relativi a posizione e orientamento.
    
    Attributes: 
        timestamp (datatime): momento in cui viene scattata la foto
        latitude (float)
        longitude (float)
        altitude (float)
        orientation (dict)
    """
    timestamp: Optional[datetime.datetime] = None
    latitude: Optional[float] = None
    longitude: Optional[float] = None
    altitude: Optional[float] = None

@dataclass
class CapturedImage:
    """
    Rappresenta l'unità atomica di dati del sistema Digital Twin.

    Questo modello incapsula i dati grezzi dell'immagine, i parametri ottici 
    della camera (intrinseci) e i riferimenti spaziali (estrinseci), fungendo 
    da ponte tra il file fisico su disco e la ricostruzione 3D finale.

    Attributes:
        image_id (str): Id univoco della foto
        file_path (str): Percorso sorgente dell'immagine originale. 
        processed_path (str): Percorso sorgente dell'immagine processata.
        file_name (str): nome del file, dato derivato dal path.
        file_extension (str): estensione del file, dato derivato dal path.
        status (Enum): Stato dell' entità immagine durante il flusso dati.
        camera_metadata (CAmeraMetadata): dati relativi alla camera utilizzata per l'immagine
        spatial_metadata (SpatialMetadata): dati relativi alla posizione e al tempo di scatto dell'immagine.
    """

    file_path: str
    image_id: str = field(default_factory=lambda: str(uuid.uuid4()))
    processed_path: Optional[str] = None

    file_name: str = field(init=False)
    file_extension: str = field(init=False)
    status: str = "RAW"

    camera_metadata: CameraMetadata = field(default_factory=CameraMetadata)
    spatial_metadata: SpatialMetadata = field(default_factory=SpatialMetadata)

    def __post_init__(self):
        """Calcoli automatici dopo la creazione dell'oggetto"""
        self.file_name = os.path.basename(self.file_path)
        self.file_extension = os.path.splitext(self.file_name)[1].lower()