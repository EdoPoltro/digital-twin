from typing import Literal
import numpy as np
import open3d as o3d
from pathlib import Path
from config import DATA_OPEN3D_EXPORTED_MODEL, DATA_OPENMVS_DEFAULT_MODEL_TEXTURED, DEFAULT_SCAN_MODE
from src.core.exceptions import Open3dError
from src.utils.log_utils import success_alert

class Open3dManager:

    def __init__(self, scan_mode: Literal['indoor', 'outdoor'] = DEFAULT_SCAN_MODE):
        self.scan_mode = scan_mode
        self.mesh = None
        o3d.utility.set_verbosity_level(o3d.utility.VerbosityLevel.Error)

    def start_full_open3d_pipeline(self, scale_real_distance: float = 1, scale_virtual_distance: float = 1, output_model_path: Path = DATA_OPEN3D_EXPORTED_MODEL, model_path: Path = DATA_OPENMVS_DEFAULT_MODEL_TEXTURED):
        """
        funzione che gestisce la pipeline di Open3D.
        """
        self.import_from_openmvs(model_path)
        if self.scan_mode == 'indoor': self.generate_resized_mesh(scale_real_distance, scale_virtual_distance)
        self.run_noise_remover()
        self.run_mesh_exporter(output_model_path)
        self.run_visualizer()

    def import_from_openmvs(self, model_path: Path = DATA_OPENMVS_DEFAULT_MODEL_TEXTURED) -> None:
        """
        Funzione che carica la mesh texturizzata generata da OpenMVS
        """
        if not model_path.exists():
            raise Open3dError('Failed to import model from OpenMVS: File not exists.')
        
        try:
            self.mesh = o3d.io.read_triangle_mesh(
                str(model_path), 
                enable_post_processing=True
            )
            success_alert('OpenMVS model imported.')
        except Exception as e:
            raise Open3dError(f'Failed to import model from OpenMVS: {e}')

    def generate_resized_mesh(self, real_distance: float = 1, virtual_distance: float = 1):
        """
        Funzione usata in indoor mode per dare una dimensione reale agli oggetti.
        """
        if not self.mesh:
            raise Open3dError('Mesh not found.')
        if self.scan_mode != 'indoor':
            raise Open3dError('Scan mode error')
        
        
        scale_factor = self._get_scale_factor(real_distance, virtual_distance)
        try:
            self.mesh.scale(scale_factor, center=(0, 0, 0))
            success_alert('Mesh scaled.')
        except Exception as e:
            raise Open3dError(f'Mesh scaling failed: {e}')

    # TODO: implmentare la funzione che fa ottenere la virtual distance 
    def _get_scale_factor(self, real_distance: float = 1, virtual_distance: float = 1) -> float:
        """
        Funzione usata in indoor mode per ottenere la scala.
        """
        if virtual_distance <= 0:
            raise Open3dError('Invalid virtual distance value.')
        return real_distance / virtual_distance
    
    def run_noise_remover(self) -> None:
        """
        Funzione usata per rimuovere i triangoli volanti che creano rumore.
        """
        if not self.mesh:
            raise Open3dError('Mesh not found.')
        
        try:
            triangle_clusters, cluster_n_triangles, _ = self.mesh.cluster_connected_triangles()
            triangle_clusters = np.asarray(triangle_clusters)
            cluster_n_triangles = np.asarray(cluster_n_triangles)

            if len(cluster_n_triangles) == 0:
                raise Exception('No cluster founded.')
            
            largest_cluster_idx = cluster_n_triangles.argmax()
            triangles_to_remove = triangle_clusters != largest_cluster_idx
            self.mesh.remove_triangles_by_mask(triangles_to_remove)
            self.mesh.remove_unreferenced_vertices()
            rumore_rimosso = len(cluster_n_triangles) - 1
            success_alert(f'Noise removed: {rumore_rimosso} cluster removed')
        except Exception as e:
            raise Open3dError(f'Noise removing failed: {e}')

    def run_mesh_exporter(self, output_model_path: Path = DATA_OPEN3D_EXPORTED_MODEL):
        """
        Funzione usata per salvare la mesh finale.
        """
        if not self.mesh:
            raise Open3dError('Mesh not found.')
        output_model_path.parent.mkdir(parents=True, exist_ok=True)

        try:
            success = o3d.io.write_triangle_mesh(
                str(output_model_path), 
                self.mesh, 
                write_triangle_uvs=True
            )
            if not success: raise Exception('exporting error.')
            success_alert('Exporting completed.')
        except Exception as e:
            raise Open3dError(f'Exporting failed: {e}')

    def run_visualizer(self) -> None:
        """
        Funzione per visualizzare il risultato della mesh
        """
        if not self.mesh:
            raise Open3dError('mesh not found.')

        try:
            o3d.visualization.draw_geometries(
                [self.mesh], 
                window_name="Open3D - Visualizzatore Modello",
                width=1024, 
                height=768,
                mesh_show_wireframe=False,
                mesh_show_back_face=True
            )
        except Exception as e:
            raise Open3dError(f'Failed to visualize model: {e}')

