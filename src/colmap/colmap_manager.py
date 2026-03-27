from pathlib import Path
from typing import Literal
from config import DATA_COLMAP_DEFAULT_CAMERAS_DATABASE, ENGINES_COLMAP_EXE, DATA_COLMAP_DEFAULT_GPS_DATA, DATA_COLMAP_ALIGNED_DIR, DATA_COLMAP_SPARSE_DIR, DATA_COLMAP_UNDISTORTED_DIR, DATA_OPENMVS_DIR, DATA_PROCESSING_PROCESSED_DIR, DEFAULT_SCAN_MODE
from src.core.exceptions import ColmapError
from src.utils.io_utils import folders_counter
from src.utils.log_utils import subprocess_execution, success_alert, warning_alert

class ColmapManager:
    """
    Classe per la gestione delle varie fasi dell'esecuzione di COLMAP

    Attributes:
        colmap_exe (Path)
        input_images_dir (Path)
        scan_mode (Literal['indoor', 'outdoor'])
    """
    def __init__(self, colmap_exe: Path = ENGINES_COLMAP_EXE, input_images_dir: Path = DATA_PROCESSING_PROCESSED_DIR, scan_mode: Literal['indoor', 'outdoor'] = DEFAULT_SCAN_MODE, sparse_dir: Path = DATA_COLMAP_SPARSE_DIR, aligned_dir: Path = DATA_COLMAP_ALIGNED_DIR, output_log: bool = False):
        self.colmap_exe = colmap_exe
        self.input_images_dir = input_images_dir
        self.scan_mode = scan_mode
        self.sparse_dir = sparse_dir
        self.aligned_dir = aligned_dir
        self.output_log = output_log

        self._run_constructor_validation()

    def _run_constructor_validation(self):
        """
        Funzione che controlla i dati assegnati allistanza di colmap manager.
        """
        if not self.colmap_exe.exists():
            raise ColmapError("File colmap.exe not found.")

        if not self.input_images_dir.is_dir():
            raise ColmapError("Input directory not found.")

        try:
            subprocess_execution([str(self.colmap_exe), "--help"], 'Validation colmap.exe.', check=False, timeout=10)
            success_alert(f'COLMAP Manager started.')
        except Exception:
            raise ColmapError("colmap.exe has crashed.") 

    def start_full_colmap_pipeline(self, cameras_db_path: Path = DATA_COLMAP_DEFAULT_CAMERAS_DATABASE, use_gpu: bool = True, gps_txt_path: Path = DATA_COLMAP_DEFAULT_GPS_DATA, undistorted_dir: Path = DATA_COLMAP_UNDISTORTED_DIR):
        """
        Funzione per gestire la pipeline di COLMAP.
        """
        self.generate_sparse_point_cloud(cameras_db_path, use_gpu)
        if self.scan_mode == 'indoor':
            self.generate_indoor_aligned_point_cloud()
        elif self.scan_mode == 'outdoor':
            self.generate_outdoor_aligned_point_cloud(gps_txt_path)
        self.generate_undistort_images(undistorted_dir)

    def generate_sparse_point_cloud(self, cameras_db_path: Path = DATA_COLMAP_DEFAULT_CAMERAS_DATABASE, use_gpu: bool = True):
        """
        Funzione per la generazione della nuvola di punti sparsa.
        """
        use_gpu_flag = "1" if use_gpu else "0"
        self._run_feature_extractor(cameras_db_path, use_gpu_flag)
        self._run_exhaustive_matcher(cameras_db_path, use_gpu_flag)
        self._run_mapper(cameras_db_path) 

    def _run_feature_extractor(self, cameras_db_path, use_gpu_flag):
        """
        Trova i punti chiave nelle immagini usando il database pre-compilato.
        """
        command = [
            str(self.colmap_exe), "feature_extractor",
            "--database_path", str(cameras_db_path),
            "--image_path", str(self.input_images_dir),
            "--ImageReader.single_camera", "1",
            "--FeatureExtraction.use_gpu", str(use_gpu_flag),
            "--FeatureExtraction.num_threads", '2'
        ]

        try:
            subprocess_execution(command, 'Extracting image features.', self.output_log)
            success_alert('Features extracted.')
        except Exception as e:
            raise ColmapError(f"Feature extraction failed: {e}")

    def _run_exhaustive_matcher(self, cameras_db_path, use_gpu_flag):
        """
        Trova le corrispondenze tra i punti delle foto vicine nel tempo.
        """
        command = [
            str(self.colmap_exe), "exhaustive_matcher",
            "--database_path", str(cameras_db_path),
            "--FeatureMatching.use_gpu", str(use_gpu_flag) 
        ]

        try:
            subprocess_execution(command, 'Matching features between images.', self.output_log)
            success_alert('Feature matching completed.')
        except Exception as e:
            raise ColmapError(f"Sequential matching failed: {e}")

    def _run_mapper(self, cameras_db_path):
        """
        Ricostruzione 3D (Structure from Motion). Genera la nuvola di punti e la posizione delle fotocamere nello spazio.
        """
        self.sparse_dir.mkdir(parents=True, exist_ok=True)

        command = [
            str(self.colmap_exe), "mapper",
            "--database_path", str(cameras_db_path),
            "--image_path", str(self.input_images_dir),
            "--output_path", str(self.sparse_dir)
        ]

        try:
            subprocess_execution(command, 'Generating sparse point cloud.', self.output_log)
            folders = folders_counter(self.sparse_dir)
        
            if folders == 0:
                raise ColmapError(f"Mapping failed: no folders generated.")
            elif folders > 1:
                warning_alert('More than 1 folder generated, verrà considerata solo la prima.')
            else:
                success_alert('Sparse reconstruction completed.')
                
        except Exception as e:
            raise ColmapError(f"Mapping failed: {e}")

    # TODO: Testare la possibilita di un alignment outdoor
    def generate_outdoor_aligned_point_cloud(self, gps_txt_path: Path = DATA_COLMAP_DEFAULT_GPS_DATA):
        """
        Funzione per la georeferenziazione. Usa il file GPS per scalare e posizionare il modello nel mondo reale. viene usata solo in outdoor mode
        """
        if not Path(gps_txt_path).exists():
            raise ColmapError("GPS data not found.")
        
        input_sparse = self.sparse_dir / '0'
        if not input_sparse.exists():
            raise ColmapError('Input dir not found.')

        output_aligned = self.aligned_dir / '0'
        output_aligned.mkdir(parents=True, exist_ok=True)

        command = [
            str(self.colmap_exe), "model_aligner",
            "--input_path", str(input_sparse),
            "--output_path", str(output_aligned),
            "--ref_images_path", str(gps_txt_path), 
            "--ref_is_gps", "1", 
            "--alignment_type", "enu",
            "--alignment_max_error", '3.0'
        ]

        try:
            subprocess_execution(command, 'Undistorting images.', self.output_log)
            success_alert('Alignement completed.')
        except Exception:
            raise ColmapError("alignement faild.")
        
    def generate_indoor_aligned_point_cloud(self):
        """
        Funzione per l'alignement in indoor mode, usata per aiutare open3d e tutta la pipeline.
        """
        input_sparse = self.sparse_dir / '0'
        if not input_sparse.exists():
            raise ColmapError('Input dir not found.')

        output_aligned = self.aligned_dir / '0'
        output_aligned.mkdir(parents=True, exist_ok=True)

        command = [
            str(self.colmap_exe), 'model_orientation_aligner',
            '--image_path', str(self.input_images_dir),
            '--input_path', str(input_sparse), 
            '--output_path', str(output_aligned), 
            '--method', 'MANHATTAN-WORLD',
            '--max_image_size', '1024',
            '--max_num_images', '100'
        ]
        
        try:
            subprocess_execution(command, 'Undistorting images.', self.output_log)
            success_alert('Alignement completed.')
        except Exception as e:
            print(f"Alignement failed.")

    def generate_undistort_images(self, undistorted_dir: Path = DATA_COLMAP_UNDISTORTED_DIR):
        """
        Filtra le immagini per togliere la distorsione dovuta dalla lente.
        """
        input_aligned = self.aligned_dir / '0'
        undistorted_dir.mkdir(parents=True, exist_ok=True)

        command = [
            self.colmap_exe.as_posix(), "image_undistorter",
            "--image_path", str(self.input_images_dir),
            "--input_path", str(input_aligned),
            "--output_path", str(undistorted_dir),
            "--output_type", "COLMAP",
            "--max_image_size", "2000"
        ]

        try: 
            subprocess_execution(command, 'Undistorting images.')
            success_alert('Images undistorted.')
        except Exception as e:
            ColmapError('Undistorting images failed.')

        command = [
            str(self.colmap_exe), "model_converter",
            "--input_path", str(undistorted_dir / "sparse"),
            "--output_path", str(undistorted_dir / "sparse"),
            "--output_type", "TXT"
        ]

        try: 
            subprocess_execution(command, 'Converting binary model.')
            success_alert('Images exported.')
        except Exception as e:
            ColmapError('Converting binary model failed.')
    
    