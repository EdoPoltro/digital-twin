from pathlib import Path
import subprocess
from config import DATA_COLMAP_DEFAULT_GPS_DATA, DATA_COLMAP_DEFAULT_EXE, DATA_COLMAP_DEFAULT_GPS_DATA, DATA_COLMAP_ALIGNED_DIR, DATA_COLMAP_SPARSE_DIR, DATA_PROCESSING_PROCESSED_DIR
from src.core.exceptions import ColmapError

# I VALORI DI CONFIG NEL COSTRUTTORE : funziona ma se voglio poi creare il manager prima di aver inizializzato il gps_data gia esplodera perche non esiste nessun file li :
# per risolvere il problema devo spostare il controllo all'inizio della generate della sparse point cloud 

# usando il il le costanti direttamente nel costruttore automaticamente importo anche il file config (problema di prestazioni semmai)

# gestione errori durante le fasi di sparse 

class ColmapManager:
    """
    Classe per la gestione delle varie fasi dell'esecuzione di colmap

    Attributes:
        gps_txt_path (Path)
        cameras_db_path (Path)
        colmap_exe (Path)
        input_images_dir (Path)
    """
    def __init__(self, gps_txt_path: Path = DATA_COLMAP_DEFAULT_GPS_DATA, cameras_db_path: Path = DATA_COLMAP_DEFAULT_GPS_DATA, colmap_exe: Path = DATA_COLMAP_DEFAULT_EXE, input_images_dir: Path = DATA_PROCESSING_PROCESSED_DIR):
        self.gps_txt_path = gps_txt_path
        self.cameras_db_path = cameras_db_path
        self.colmap_exe = colmap_exe
        self.input_images_dir = input_images_dir
        self._run_constructor_validation()

    def start_full_colmap_pipeline(self, sparse_dir: Path = DATA_COLMAP_SPARSE_DIR, aligned_dir: Path = DATA_COLMAP_ALIGNED_DIR, images_overlap: int = 10, use_gpu: bool = False, threads_number: int = 2): # full
        self.generate_sparse_point_cloud(sparse_dir, aligned_dir, images_overlap, use_gpu, threads_number)
        self.generate_dense_point_cloud()
        self.generate_mesh()

    def generate_sparse_point_cloud(self, sparse_dir: Path = DATA_COLMAP_SPARSE_DIR, aligned_dir: Path = DATA_COLMAP_ALIGNED_DIR, images_overlap: int = 10, use_gpu: bool = False, threads_number: int = 2): # fase 1
        use_gpu_flag = "1" if use_gpu else "0"
        self._run_feature_extractor(use_gpu_flag, threads_number)
        self._run_sequential_matcher(use_gpu_flag, images_overlap)
        self._run_mapper(sparse_dir) 
        self._run_model_aligner(aligned_dir, sparse_dir)

    def generate_dense_point_cloud(self):
        pass # fase 2

    def generate_mesh(self):
        pass # fase 3

    def _run_feature_extractor(self, use_gpu_flag, threads_number):
        """Fase 1: Trova i punti chiave nelle immagini usando il database pre-compilato."""
        command = [
            str(self.colmap_exe), "feature_extractor",
            "--database_path", str(self.cameras_db_path),
            "--image_path", str(self.input_images_dir),
            "--FeatureExtraction.use_gpu", str(use_gpu_flag),
            "--FeatureExtraction.num_threads", str(threads_number)
        ]
        subprocess.run(command, check=True)

    def _run_sequential_matcher(self, use_gpu_flag, images_overlap: int):
        """Fase 2: Trova le corrispondenze tra i punti delle foto vicine nel tempo."""
        command = [
            str(self.colmap_exe), "sequential_matcher",
            "--database_path", str(self.cameras_db_path),
            "--SequentialMatching.overlap", str(images_overlap),
            "--FeatureMatching.use_gpu", str(use_gpu_flag) 
        ]
        subprocess.run(command, check=True)

    def _run_mapper(self, output_sparse_dir: Path):
        """Fase 3: Ricostruzione 3D (Structure from Motion). Genera la nuvola di punti e la posizione delle fotocamere nello spazio."""
        output_sparse_dir.mkdir(parents=True, exist_ok=True)
        command = [
            str(self.colmap_exe), "mapper",
            "--database_path", str(self.cameras_db_path),
            "--image_path", str(self.input_images_dir),
            "--output_path", str(output_sparse_dir)
        ]
        subprocess.run(command, check=True)

    # da verificare perche mi sa che va usato solo in uno spazio un po piu ampio di qualche metro 
    # TODO: da fixxare 
    def _run_model_aligner(self, output_aligned_dir: Path, input_sparse_dir: Path):
        """Fase 4: Georeferenziazione. Usa il file GPS per scalare e posizionare il modello nel mondo reale."""
        output_aligned_dir.mkdir(parents=True, exist_ok=True)
        command = [
            str(self.colmap_exe), "model_aligner",
            "--input_path", str(input_sparse_dir / "0"),
            "--output_path", str(output_aligned_dir),
            "--ref_images_path", str(self.gps_txt_path),
            "--ref_is_gps", "1", 
            "--alignment_type", "ecef",
            "--alignment_max_error", "100.0",     
            "--min_common_images", "3"            
        ]
        subprocess.run(command, check=True)


    def _run_constructor_validation(self):
        """Funzione che controlla i dati assegnati allistanza di colmap manager"""
        if self.colmap_exe.is_absolute() and not self.colmap_exe.exists():
            raise ColmapError("File colmap.exe not found.")
        
        if not Path(self.cameras_db_path).exists():
            raise ColmapError("Database not found.")
            
        if not Path(self.gps_txt_path).exists():
            raise ColmapError("GPS data not found.")

        if not Path(self.input_images_dir).is_dir():
            raise ColmapError("Input directory not found.")

        try:
            command = [str(self.colmap_exe), "help"]
            subprocess.run(command,  capture_output=True, text=True, check=True)
        except (subprocess.CalledProcessError, FileNotFoundError, OSError) as e: 
            raise ColmapError("colmap.exe has crashed.")
        

    