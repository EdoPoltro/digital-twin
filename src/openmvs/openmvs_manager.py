from pathlib import Path
from src.core.exceptions import OpenmvsError
from src.utils.log_utils import success_alert, subprocess_execution
from config import (
    BASE_DIR, 
    DATA_COLMAP_UNDISTORTED_DIR, 
    DATA_OPENMVS_ALIGNED_MVS, 
    DATA_OPENMVS_DENSE_MVS,
    DATA_OPENMVS_DENSE_PLY,
    DATA_OPENMVS_MESH_MVS,
    DATA_OPENMVS_MESH_PLY,
    DATA_OPENMVS_REFINE_MVS,
    DATA_OPENMVS_REFINE_PLY,
    DATA_OPENMVS_TEXTURE_MVS, 
    ENGINES_OPENMVS_DENSE_EXE, 
    DATA_OPENMVS_DIR, 
    ENGINES_OPENMVS_INTERFACE_EXE,
    ENGINES_OPENMVS_RECONSTRUCT_MESH_EXE,
    ENGINES_OPENMVS_REFINE_MESH_EXE,
    ENGINES_OPENMVS_TEXTURE_MESH_EXE
)

class OpenmvsManager:
    """
    Classe per la gestione delle varie fasi dell'esecuzione di OpenMVS
    """
    def __init__(
            self, 
            openmvs_dense_exe: Path = ENGINES_OPENMVS_DENSE_EXE, 
            openmvs_interface_exe: Path = ENGINES_OPENMVS_INTERFACE_EXE, 
            openmvs_reconstruct_mesh_exe: Path = ENGINES_OPENMVS_RECONSTRUCT_MESH_EXE,
            openmvs_refine_mesh_exe: Path = ENGINES_OPENMVS_REFINE_MESH_EXE,
            openmvs_texture_mesh_exe: Path = ENGINES_OPENMVS_TEXTURE_MESH_EXE,
            openmvs_dir: Path = DATA_OPENMVS_DIR, 
            input_dir: Path = DATA_COLMAP_UNDISTORTED_DIR,
            output_log: bool = True,
            aligned_mvs: Path = DATA_OPENMVS_ALIGNED_MVS,
            dense_mvs: Path = DATA_OPENMVS_DENSE_MVS,
            dense_ply: Path = DATA_OPENMVS_DENSE_PLY,
            mesh_mvs: Path = DATA_OPENMVS_MESH_MVS,
            mesh_ply: Path = DATA_OPENMVS_MESH_PLY,
            refine_mvs: Path = DATA_OPENMVS_REFINE_MVS,
            refine_ply: Path = DATA_OPENMVS_REFINE_PLY,
            texture_mvs: Path = DATA_OPENMVS_TEXTURE_MVS  
        ):
        self.openmvs_dense_exe = openmvs_dense_exe
        self.openmvs_interface_exe = openmvs_interface_exe
        self.openmvs_reconstruct_mesh_exe = openmvs_reconstruct_mesh_exe
        self.openmvs_refine_mesh_exe = openmvs_refine_mesh_exe
        self.openmvs_texture_mesh_exe = openmvs_texture_mesh_exe
        self.openmvs_dir = openmvs_dir
        self.input_dir = input_dir
        self.aligned_mvs = aligned_mvs
        self.dense_mvs = dense_mvs
        self.dense_ply = dense_ply
        self.mesh_mvs = mesh_mvs 
        self.mesh_ply = mesh_ply
        self.refine_mvs = refine_mvs
        self.refine_ply = refine_ply
        self.texture_mvs = texture_mvs
        self.output_log = output_log
        self._run_constructor_validation()

    def start_full_openmvs_pipeline(self):
        """
        Funzione che importa il modello da colmap e genera la nuvola densa.
        """
        self.run_colmap_importer()
        self.run_dense_generator()
        self.run_mesh_generator()
        self.run_mesh_refiner()
        self.run_mesh_texturizer()

    def run_colmap_importer(self):
        """
        Converte le immagini senza distorzione di COLMAP nel formato .mvs.
        """
        self.openmvs_dir.mkdir(parents=True, exist_ok=True)

        command = [
            str(self.openmvs_interface_exe),
            "-i", str(self.input_dir),
            "-o", str(self.aligned_mvs),
            "--image-folder", str(self.input_dir / "images"),
        ]

        try:
            subprocess_execution(command, "Importing COLMAP model.", output_log = self.output_log)
            success_alert('COLMAP model imported.')
            self._log_cleanup()
        except Exception as e:
            raise OpenmvsError(f'Failed to import model from COLMAP: {e}')

    def run_dense_generator(self):
        """
        Trasforma la nuvola sparsa in una nuvola densa (milioni di punti).
        """

        if not self.aligned_mvs.exists():
            raise OpenmvsError(f"File model.mvs not found.")

        command = [
            str(self.openmvs_dense_exe), str(self.aligned_mvs.name),
            "-o", str(self.dense_mvs.name),
            "--resolution-level", "0"
        ]

        try:
            subprocess_execution(command, 'Dense point cloud generating.', output_log = self.output_log, cwd=self.openmvs_dir)
            success_alert('Dense point cloud generated.')
            self._log_cleanup()
        except Exception as e:
            raise OpenmvsError(f"Error generating dense point cloud: {e}")

    def run_mesh_generator(self):
        """
        Funzione per la costruizone della mesh.
        """
        if not self.dense_mvs.exists:
            raise OpenmvsError(f"File dense.mvs not found.")
        
        command = [
            str(self.openmvs_reconstruct_mesh_exe), str(self.dense_mvs.name),
            '--archive-type', '2',
            '-o', str(self.mesh_mvs.name),
            '--thickness-factor', '1.5',
            '--min-point-distance', '2',
            "-p", str(self.dense_ply.name)
        ]

        try:
            subprocess_execution(command, 'Mesh generating.', output_log = self.output_log, cwd=self.openmvs_dir)
            success_alert('Mesh generated.')
            self._log_cleanup()
        except Exception:
            raise OpenmvsError("Mesh reconstruction failed.")

    def run_mesh_refiner(self):
        """
        Funzione per rifinire la mesh.
        """
        if not self.mesh_mvs.exists:
            raise OpenmvsError(f"File mesh.mvs not found.")
        
        command = [
            str(self.openmvs_refine_mesh_exe), str(self.mesh_mvs.name),
            '-o', str(self.refine_mvs.name),
            '-m', str(self.mesh_ply.name)
        ]

        try:
            subprocess_execution(command, 'Mesh refining.', output_log = self.output_log, cwd=self.openmvs_dir)
            success_alert('Mesh refined.')
            self._log_cleanup()
        except Exception:
            raise OpenmvsError("Mesh refining failed.")
    
    def run_mesh_texturizer(self):
        """
        Funzione per generare la texture.
        Nota: i flag '--local-seam-leveling 0' e '--global-seam-leveling 0' sono obbligatori per un bug della versione 2.4
        """
        if not self.refine_mvs.exists:
            raise OpenmvsError(f"File refine.mvs not found.")
        
        command = [
            str(self.openmvs_texture_mesh_exe), str(self.refine_mvs.name),
            '-o', str(self.texture_mvs.name),
            '-m', str(self.refine_ply.name),
            '--export-type', 'obj',
            '--local-seam-leveling', '0',
            '--global-seam-leveling', '0',
            '--max-texture-size', '8192'
        ]

        try:
            subprocess_execution(command, 'Mesh texturing.', output_log = self.output_log, cwd=self.openmvs_dir)
            success_alert('Mesh textured.')
            self._log_cleanup()
        except Exception:
            raise OpenmvsError("Mesh texturing failed.")
        
    def _run_constructor_validation(self):
        """
        Funzione che controlla i dati assegnati allistanza di openMVS manager.
        """
        if not self.openmvs_dense_exe.exists():
            raise OpenmvsError("File DensifyPointCloud.exe not found.")
        
        if not self.openmvs_interface_exe.exists():
            raise OpenmvsError("File InterfaceCOLMAP.exe not found.")
        
        if not self.openmvs_reconstruct_mesh_exe.exists():
            raise OpenmvsError("File ReconstructMesh.exe not found.")
        
        if not self.openmvs_refine_mesh_exe.exists():
            raise OpenmvsError("File RefineMesh.exe not found.")
        
        if not self.openmvs_texture_mesh_exe.exists():
            raise OpenmvsError("File TextureMesh.exe not found.")
        
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