from pathlib import Path
import subprocess
from config import BASE_DIR, DATA_OPENMVS_DEFAULT_MODEL, DATA_OPENMVS_DEFAULT_MODEL_DENSE, DATA_OPENMVS_DEFAULT_MODEL_MESH_MVS, DATA_OPENMVS_DEFAULT_MODEL_MESH_PLY, DATA_OPENMVS_DEFAULT_MODEL_TEXTURIZED, DATA_OPENMVS_DENSE_DEFAULT_EXE, DATA_OPENMVS_DIR, DATA_OPENMVS_INTERFACE_EXE, DATA_OPENMVS_MESH_RECONSTRUCTOR_DEFAULT_EXE, DATA_OPENMVS_MESH_TEXTURIZER_DEFAULT_EXE
from src.core.exceptions import OpenmvsError
from src.utils.logging_utils import error_alert, log_alert

class OpenmvsManager:
    def __init__(self, openmvs_dense_exe: Path = DATA_OPENMVS_DENSE_DEFAULT_EXE, openmvs_mesh_reconstructor_exe: Path = DATA_OPENMVS_MESH_RECONSTRUCTOR_DEFAULT_EXE, openmvs_interface_exe: Path = DATA_OPENMVS_INTERFACE_EXE, openmvs_mesh_texturizer_exe: Path = DATA_OPENMVS_MESH_TEXTURIZER_DEFAULT_EXE , openmvs_dir: Path = DATA_OPENMVS_DIR):
        self.openmvs_dense_exe = openmvs_dense_exe
        self.openmvs_mesh_reconstructor_exe = openmvs_mesh_reconstructor_exe
        self.openmvs_mesh_texturizer_exe = openmvs_mesh_texturizer_exe
        self.openmvs_interface_exe = openmvs_interface_exe
        self.openmvs_dir = openmvs_dir

        self._run_constructor_validation()
        log_alert(f'OpenMVS Manager avviato.')

    def start_full_openmvs_pipeline(self):
        pass

    def import_from_colmap(self, colmap_input_dir: Path):
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
        subprocess.run(command, check=True)
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
            "--max-threads", "0"          
        ]
        subprocess.run(command, check=True)
        self._log_cleanup()

    def clean_point_cloud(self):
        pass

    def reconstruct_mesh(self, input_model_dense: Path = DATA_OPENMVS_DEFAULT_MODEL_DENSE, output_model_mesh: Path = DATA_OPENMVS_DEFAULT_MODEL_MESH_MVS):
        """
        Trasforma la nuvola di punti densa in una mesh di triangoli.
        """
        command = [
            str(self.openmvs_mesh_reconstructor_exe),
            str(input_model_dense),
            "-o", str(output_model_mesh),
            "-w", str(self.openmvs_dir)
        ]
        subprocess.run(command, check=True)
        self._log_cleanup()

    def texture_mesh_from_colmap(self, input_model: Path = DATA_OPENMVS_DEFAULT_MODEL, input_model_mesh: Path = DATA_OPENMVS_DEFAULT_MODEL_MESH_PLY, output_model_texturized: Path = DATA_OPENMVS_DEFAULT_MODEL_TEXTURIZED):
        """
        Funzione che applica le texture delle foto originali sulla mesh.
        """
        command = [
            str(self.openmvs_mesh_texturizer_exe),
            str(input_model),
            "--mesh-file", str(input_model_mesh),
            "-o", str(output_model_texturized),
            "-w", str(self.openmvs_dir),
            "--export-type", "obj"
        ]
        subprocess.run(command, check=True)
        self._log_cleanup()

    def _run_constructor_validation(self):
        """Funzione che controlla i dati assegnati allistanza di openMVS manager."""
        if not self.openmvs_dense_exe.exists():
            raise OpenmvsError("File DensifyPointCloud.exe not found.")
        
        if not self.openmvs_mesh_reconstructor_exe.exists():
            raise OpenmvsError("File ConstructMesh.exe not found.")
        
        if not self.openmvs_mesh_texturizer_exe.exists():
            raise OpenmvsError("File TextureMesh.exe not found.")
    
        if not self.openmvs_interface_exe.exists():
            raise OpenmvsError("File InterfaceCOLMAP.exe not found.")
        
        try:
            subprocess.run([str(self.openmvs_dense_exe), "--help", "-v", "0",], creationflags=subprocess.CREATE_NO_WINDOW, timeout=5)
        except Exception:
            raise OpenmvsError(f"DensifyPointCloud.exe has crashed.")
        
        # try:
        #     subprocess.run([str(self.openmvs_mesh_reconstructor_exe), "--help", "-v", "0",], capture_output=True, timeout=5)
        # except Exception:
        #     raise OpenmvsError(f"ConstructorMesh.exe has crashed.")
        
        # try:
        #     subprocess.run([str(self.openmvs_mesh_texturizer_exe), "--help", "-v", "0",], capture_output=True, timeout=5)
        # except Exception:
        #     raise OpenmvsError(f"TextureMesh.exe has crashed.")
        
        # try:
        #     subprocess.run([str(self.openmvs_interface_exe), "--help", "-v", "0",], capture_output=True, timeout=5)
        # except Exception:
        #     raise OpenmvsError(f"InterfaceCOLMAP.exe has crashed.")
        
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

        