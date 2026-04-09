from typing import Literal
import numpy as np
import open3d as o3d
from pathlib import Path
from src.core.exceptions import Open3dError
from src.utils.log_utils import Loader, success_alert, warning_alert
from config import (
    
    DATA_OPEN3D_DIR,
    DATA_OPEN3D_MODEL_OBJ,
    DATA_OPEN3D_MODEL_PLY,
    DATA_OPENMVS_TEXTURE_OBJ,
    DEFAULT_SCAN_MODE
)
class Open3dManager:
    """
    Classe per la gestione delle varie fasi dell'esecuzione di Open3D.
    """
    def __init__(
            self, 
            texture_obj: Path = DATA_OPENMVS_TEXTURE_OBJ,
            open3d_dir: Path = DATA_OPEN3D_DIR,
            scan_mode: Literal['indoor', 'outdoor'] = DEFAULT_SCAN_MODE,
            scale_real_distance: float = 1,
            scale_virtual_distance: float = 1,
            model_smoothing_iterations: int = 2,
            model_flip: bool = False,
            model_aligne: bool = True,
            model_scale: bool = False,
            model_plane: bool = True,
            model_axis: Literal['X', 'Y', 'Z'] = 'Y',
            model_ply: Path = DATA_OPEN3D_MODEL_PLY,
            model_obj: Path = DATA_OPEN3D_MODEL_OBJ
        ):
        self.texture_obj = texture_obj
        self.open3d_dir = open3d_dir
        self.scan_mode = scan_mode
        self.scale_real_distance = scale_real_distance
        self.scale_virtual_distance = scale_virtual_distance
        self.model_smoothing_iterations = model_smoothing_iterations
        self.model_flip = model_flip
        self.model_aligne = model_aligne
        self.model_scale = model_scale
        self.model_plane = model_plane
        self.model_axis = model_axis
        self.model_ply = model_ply
        self.model_obj = model_obj
        self._model = None
        self._loader = Loader()
        o3d.utility.set_verbosity_level(o3d.utility.VerbosityLevel.Error)

    def start_full_open3d_pipeline(self):
        """
        funzione che gestisce la pipeline di Open3D.
        """
        self.run_model_importer()
        self.run_model_topological_cleaner()
        self.run_model_noise_remover()
        self.run_model_aligner()
        self.run_model_scaler()
        self.run_model_smoother()
        self.run_model_exporter()

    def run_model_importer(self):
        """
        Funzione per l'importazione del modello .obj da openmvs.
        """
        self._loader.start('Model Importing.')
        
        try:
            self._model = o3d.io.read_triangle_mesh(str(self.texture_obj), enable_post_processing=True)

            if self._model.is_empty():
                raise Open3dError('Model loaded is empty.')
            
            if not self._model.has_triangle_uvs():
                self._loader.stop()
                warning_alert('No UV data detected.')

            self._loader.stop()
            success_alert('Importation completed.')
        except Exception:
            self._loader.stop()
            raise Open3dError('Importation failed.')

    def run_model_topological_cleaner(self):
        """
        Funzione per la pulizia topologica del modello.
        Nota: non sto spostando i vertici ma sto solo rimuovendo quelli che non hanno senso di esistere.
        """
        if not self._model:
            raise Open3dError('Model not found.')
        
        self._loader.start('Topological cleaning.')

        try:
            self._model.remove_degenerate_triangles()
            self._model.remove_duplicated_triangles()
            self._model.remove_duplicated_vertices()
            self._model.remove_unreferenced_vertices()
            self._loader.stop()
            success_alert('Topological cleaning compleated.')
        except Exception:
            self._loader.stop()
            raise Open3dError('Topological cleaning failed.')

    def run_model_noise_remover(self):
        """
        Funzione per rimuovere il rumore dal modello.
        Nota: potrebbe diminuire le prestazioni finali della texture se usata con parametri troppo aggressivi.
        Implmentato in questo modeo tiene conto solo della scena con piu triangoli, se tengo conto di più pezzi separati allora dovrò
        modificare la logica per filtrare solo quelli con meno di N clusters.
        """
        if not self._model:
            raise Open3dError('Model not found.')
        
        self._loader.start('Noise removing.')
        
        try:
            triangle_clusters, cluster_n_triangles, _ = self._model.cluster_connected_triangles()
            triangle_clusters = np.asarray(triangle_clusters)
            cluster_n_triangles = np.asarray(cluster_n_triangles)

            if len(cluster_n_triangles) > 1:
                largest_cluster_idx = cluster_n_triangles.argmax()
                triangles_to_remove = triangle_clusters != largest_cluster_idx
                self._model.remove_triangles_by_mask(triangles_to_remove)
                self._model.remove_unreferenced_vertices()
                # n_rimossi = len(cluster_n_triangles) - 1

            self._loader.stop()
            success_alert('Noise removal compleated.')
        except Exception:
            self._loader.stop()
            raise Open3dError('Noise removal failed.')

    def run_model_aligner(self):
        """
        Funzione per allineare il modello correttamente.
        Nota: probabilmente il grosso del lavoro è ruotare di 180° il modello, il piano viene già trovato da COLMAP.
        """
        if not self._model:
            raise Open3dError('Model not found.')
        
        self._loader.start('Aligning.')
        
        try:
            if self.model_flip:
                R = self._model.get_rotation_matrix_from_xyz((np.pi, 0, 0))
                self._model.rotate(R, center=self._model.get_center())

            if self.model_plane: 
                self._ransac_model_plane()

            if self.model_aligne:
                min_bound = self._model.get_min_bound()
                self._model.translate((0, 0, -min_bound[2]))

            self._loader.stop()
            success_alert('Aligning compleated.')
        except Exception:
            self._loader.stop()
            raise Open3dError('Aligning failed.')

    def run_model_scaler(self):
        """
        Funzione per ridimensionare il modello.
        """
        if not self.model_scale:
            return

        if self.scan_mode == 'outdoor':
            return

        if not self._model:
            raise Open3dError('Model not found.')
        
        self._loader.start('Scaling.')

        scale_factor = self._get_scale_factor(self.scale_real_distance, self.scale_virtual_distance)
        
        try:
            self._model.scale(scale_factor, center=(0, 0, 0))
            self._loader.stop()
            success_alert('Scaling compleated.')
        except Exception:
            self._loader.stop()
            raise Open3dError('Scaling failed.')

    def run_model_smoother(self):
        """
        Funzione per pulire gli spigoli del modello.
        Nota: per file .obj evitare la smooth laplatian ma usare la smooth taubin.
        """
        if not self._model:
            raise Open3dError('Model not found.')
        
        self._loader.start('Smoothing.')
        
        try:
            original_uvs = np.asarray(self._model.triangle_uvs).copy()
            backup_textures = [o3d.geometry.Image(t) for t in self._model.textures]
            self._model = self._model.filter_smooth_taubin(number_of_iterations=self.model_smoothing_iterations)
            self._model.triangle_uvs = o3d.utility.Vector2dVector(original_uvs)
            self._model.textures = backup_textures
            self._model.compute_vertex_normals()
            self._loader.stop()
            success_alert('Smoothing compleated.')
        except Exception:
            self._loader.stop()
            raise Open3dError('Smoothing failed.')

    def run_model_exporter(self):
        """
        Funzione che riesporta il file in un .obj processato + .ply.
        """
        if not self._model:
            raise Open3dError('Model not found.')
        
        self.open3d_dir.mkdir(parents=True, exist_ok=True)
        
        self._loader.start('Model exporting.')
        
        try:
            o3d.io.write_triangle_mesh(
                str(self.model_obj),
                self._model,
                write_ascii=True,
                write_vertex_normals=True,
                write_vertex_colors=True
            )
            o3d.io.write_triangle_mesh(
                str(self.model_ply), 
                self._model, 
                write_ascii=False
            )
            self._loader.stop()
            success_alert('Exportation compleated.')
        except Exception:
            self._loader.stop()
            raise Open3dError('Exportation failed.')

    def _get_scale_factor(self, real_distance: float, virtual_distance: float) -> float:
        """
        Funzione usata in indoor mode per ottenere il fattore di scala.
        """
        if virtual_distance <= 0 or real_distance <= 0:
            raise Open3dError('Invalid distance value.')
        return real_distance / virtual_distance

    def _ransac_model_plane(self):
        """
        Funzione usata per riconoscere il piano del modello e per metterlo parallelo ad un asse a scelta.
        """
        target_axis=self.model_axis
        pcd = o3d.geometry.PointCloud()
        pcd.points = self._model.vertices
        plane_model, _ = pcd.segment_plane(distance_threshold=0.01, ransac_n=3, num_iterations=1000)
        [a, b, c, d] = plane_model
        normal = np.array([a, b, c])

        if target_axis == 'Z':
            destination = np.array([0, 0, 1])
        elif target_axis == 'Y':
            destination = np.array([0, 1, 0])
        else:
            destination = np.array([1, 0, 0])

        v = np.cross(normal, destination)
        s = np.linalg.norm(v)
        c_val = np.dot(normal, destination)

        if s > 1e-6:
            vx = np.array([[0, -v[2], v[1]], [v[2], 0, -v[0]], [-v[1], v[0], 0]])
            R = np.eye(3) + vx + np.dot(vx, vx) * ((1 - c_val) / (s**2))
            self._model.rotate(R, center=self._model.get_center())