from typing import Literal
import numpy as np
import open3d as o3d
from pathlib import Path
from config import DATA_OPEN3D_MESH_OBJ, DATA_OPEN3D_MESH_PLY, DATA_OPENMVS_DENSE_PLY, DEFAULT_SCAN_MODE
from src.core.exceptions import Open3dError
from src.utils.log_utils import success_alert, warning_alert

class Open3dManager:

    def __init__(self, scan_mode: Literal['indoor', 'outdoor'] = DEFAULT_SCAN_MODE):
        self.scan_mode = scan_mode
        self.mesh = None
        o3d.utility.set_verbosity_level(o3d.utility.VerbosityLevel.Error)

    def start_full_open3d_pipeline(self, scale_real_distance: float = 1, output_model_path: Path = DATA_OPEN3D_MESH_OBJ, input_dense_path: Path = DATA_OPENMVS_DENSE_PLY, output_mesh_path: Path = DATA_OPEN3D_MESH_PLY):
        """
        funzione che gestisce la pipeline di Open3D.
        """
        self.generate_mesh_from_openmvs(input_dense_path, output_mesh_path)
        if self.scan_mode == 'indoor': self.generate_scaled_mesh(scale_real_distance)
        self.run_noise_remover()
        self.run_mesh_exporter(output_model_path)
        self.run_visualizer()

    def import_mesh(self, input_mesh: Path = DATA_OPEN3D_MESH_PLY):
        try:
            self.mesh = o3d.io.read_triangle_mesh(
                str(input_mesh), 
                enable_post_processing=True
            )   
        except Exception as e:
            raise Open3dError(f'Import failed: {e}')

    def generate_mesh_from_openmvs(self, input_dense: Path = DATA_OPENMVS_DENSE_PLY, output_mesh: Path = DATA_OPEN3D_MESH_PLY):
        """
        Funzione che trasforma una nuvola densa in una mesh tramite l'algoritmo di poisson.
        """
        if not input_dense.exists():
            raise Open3dError(f"Point cloud file not found: {input_dense}.")
        
        try:
            dense = o3d.io.read_point_cloud(str(input_dense))

            dense.estimate_normals(search_param=o3d.geometry.KDTreeSearchParamHybrid(radius=0.1, max_nn=30))

            dense.orient_normals_towards_camera_location(camera_location=np.array([0, 0, 0]))

            dense.orient_normals_consistent_tangent_plane(10)

            mesh, densities = o3d.geometry.TriangleMesh.create_from_point_cloud_poisson(dense, depth=9)

            densities = np.asarray(densities)
            vertices_to_remove = densities < np.quantile(densities, 0.05)
            mesh.remove_vertices_by_mask(vertices_to_remove)

            self.mesh = mesh
            input_dense.parent.mkdir(parents=True, exist_ok=True)
            o3d.io.write_triangle_mesh(str(output_mesh), self.mesh)
            
            success_alert(f'Mesh generated.')
        except Exception as e:
            raise Open3dError(f"Mesh reconstruction failed: {e}")

    def generate_scaled_mesh(self, real_distance: float = 1):
        """
        Funzione usata in indoor mode per dare una dimensione reale agli oggetti.
        """
        if not self.mesh:
            raise Open3dError('Mesh not found.')
        
        if self.scan_mode != 'indoor':
            raise Open3dError('Scan mode error')
        
        virtual_distance = self._get_virtual_distance()
        
        scale_factor = self._get_scale_factor(real_distance, virtual_distance)

        if scale_factor == 1: 
            warning_alert('Scale factor: 1.')
            return

        try:
            self.mesh.scale(scale_factor, center=(0, 0, 0))
            success_alert('Mesh scaled.')
        except Exception as e:
            raise Open3dError(f'Mesh scaling failed: {e}')

    def _get_scale_factor(self, real_distance: float = 1, virtual_distance: float = 1) -> float:
        """
        Funzione usata in indoor mode per ottenere la scala.
        """
        if virtual_distance <= 0:
            raise Open3dError('Invalid virtual distance value.')
        return real_distance / virtual_distance
    
    def _get_virtual_distance(self) -> float:
        """
        Funzione per ottenere in modo interattivo la virtual distance tra due punti.
        Premere shift e tasto sinistro per settare due punti.
        """
        if not self.mesh:
            raise Open3dError("Mesh not found.")

        pcd = o3d.geometry.PointCloud()
        pcd.points = self.mesh.vertices
    
        if self.mesh.has_vertex_colors():
            pcd.colors = self.mesh.vertex_colors

        try:
            vis = o3d.visualization.VisualizerWithEditing()
            vis.create_window(window_name="Scaling", width=1280, height=720)
            vis.add_geometry(pcd)
            vis.run() 
            vis.destroy_window()
            picked_indices = vis.get_picked_points().index

            if len(picked_indices) < 2:
                raise Open3dError('Scaling failed: no enough points captured.')

            idx_start = picked_indices[0]   
            idx_end = picked_indices[-1]    
            p_start = np.asarray(pcd.points)[idx_start]
            p_end = np.asarray(pcd.points)[idx_end]
            virtual_dist = np.linalg.norm(p_start - p_end)
            
            success_alert('Points captured.')
            return virtual_dist

        except Exception as e:
            raise Open3dError(f"Scaling failed: {e}")
    
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
                raise Exception('No cluster found.')
            
            largest_cluster_idx = cluster_n_triangles.argmax()
            triangles_to_remove = triangle_clusters != largest_cluster_idx
            self.mesh.remove_triangles_by_mask(triangles_to_remove)
            self.mesh.remove_unreferenced_vertices()
            rumore_rimosso = len(cluster_n_triangles) - 1
            success_alert(f'Noise removed: {rumore_rimosso} cluster removed')
        except Exception as e:
            raise Open3dError(f'Noise removing failed: {e}')

    def run_mesh_exporter(self, output_model_path: Path = DATA_OPEN3D_MESH_OBJ):
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

