from pathlib import Path
from config import BASE_DIR, DATA_COLMAP_UNDISTORTED_DIR, DATA_OPENMVS_DENSE_DEFAULT_EXE, DATA_OPENMVS_DIR, DATA_OPENMVS_INTERFACE_EXE
from src.core.exceptions import OpenmvsError
from src.utils.log_utils import success_alert, subprocess_execution

class OpenmvsManager:
    def __init__(self, openmvs_dense_exe: Path = DATA_OPENMVS_DENSE_DEFAULT_EXE, openmvs_interface_exe: Path = DATA_OPENMVS_INTERFACE_EXE, openmvs_dir: Path = DATA_OPENMVS_DIR, output_log: bool = True):
        self.openmvs_dense_exe = openmvs_dense_exe
        self.openmvs_interface_exe = openmvs_interface_exe
        self.openmvs_dir = openmvs_dir
        self.output_log = output_log

        self._run_constructor_validation()

    def start_full_openmvs_pipeline(self, colmap_input_dir: Path = DATA_COLMAP_UNDISTORTED_DIR):
        self.import_from_colmap(colmap_input_dir)
        self.generate_dense_point_cloud()

    def import_from_colmap(self, colmap_input_dir: Path = DATA_COLMAP_UNDISTORTED_DIR):
        """
        Converte le immagini senza distorzione di COLMAP nel formato .mvs.

        Args:
            colmap_input_dir (Path)
        """
        self.openmvs_dir.mkdir(parents=True, exist_ok=True)
        output_mvs = self.openmvs_dir / "model.mvs"

        command = [
            str(self.openmvs_interface_exe),
            "-i", str(colmap_input_dir),
            "-o", str(output_mvs),
            "-w", str(self.openmvs_dir),
            "--image-folder", str(colmap_input_dir / "images")
        ]

        try:
            subprocess_execution(command, "Importing COLMAP model.", output_log = self.output_log)
            success_alert('COLMAP model imported.')
        except Exception as e:
            raise OpenmvsError(f'Failed to import model from COLMAP: {e}')
        self._log_cleanup()

    def generate_dense_point_cloud(self):
        """
        Trasforma la nuvola sparsa in una nuvola densa (milioni di punti).
        """
        input_mvs = self.openmvs_dir / "model.mvs"
        output_mvs = self.openmvs_dir / "model_dense.mvs"

        if not input_mvs.exists():
            raise OpenmvsError(f"File model.mvs non trovato in: {input_mvs}")

        command = [
            str(self.openmvs_dense_exe), 
            str(input_mvs),
            "-o", str(output_mvs),
            "-w", str(self.openmvs_dir),
            "--archive-type", "1",      
            "--resolution-level", "0",  
            "--number-views", "0",        
            "--max-threads", "0",      
            "--number-views-fuse", "2"    
        ]

        try:
            subprocess_execution(command, 'Dense point cloud generating.', output_log = self.output_log)
            success_alert('Dense point cloud generated.')
        except Exception as e:
            raise OpenmvsError(f"Error generating dense point cloud: {e}")
        self._log_cleanup()
        
    def _run_constructor_validation(self):
        """
        Funzione che controlla i dati assegnati allistanza di openMVS manager.
        """
        if not self.openmvs_dense_exe.exists():
            raise OpenmvsError("File DensifyPointCloud.exe not found.")
        
        if not self.openmvs_interface_exe.exists():
            raise OpenmvsError("File InterfaceCOLMAP.exe not found.")
        
        try:
            subprocess_execution([str(self.openmvs_dense_exe), "--help", "-v", "0",], check=False, timeout=5)
        except Exception:
            raise OpenmvsError(f"DensifyPointCloud.exe has crashed.")
        
        try:
            subprocess_execution([str(self.openmvs_interface_exe), "--help", "-v", "0",], check=False, timeout=5)
        except Exception:
            raise OpenmvsError(f"InterfaceCOLMAP.exe has crashed.")
        
        success_alert(f'OpenMVS Manager started.')
        self._log_cleanup()

    def _log_cleanup(self):
        """
        Funzione per la rimozione totale dei file log, tmp e dmp ovunque si nascondano.
        """
        directories_to_scan = [BASE_DIR, Path.cwd()]
        files_to_delete = []
        
        for directory in directories_to_scan:
            files_to_delete.extend(directory.rglob("*.log"))
            files_to_delete.extend(directory.rglob("*.tmp"))
            files_to_delete.extend(directory.rglob("*.dmp"))
            files_to_delete.extend(directory.rglob("project.ini")) 
            
        files_to_delete = list(set(files_to_delete))
        
        if not files_to_delete:
            return

        for file_path in files_to_delete:
            try:
                file_path.unlink()
            except PermissionError:
                pass
            except Exception as e:
                print(f"⚠️ Errore imprevisto durante l'eliminazione di {file_path.name}: {e}")

        