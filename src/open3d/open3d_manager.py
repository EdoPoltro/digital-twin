from typing import Literal
import numpy as np
import open3d as o3d
from pathlib import Path
from src.core.exceptions import Open3dError
from src.utils.log_utils import success_alert, warning_alert
from config import (
    DATA_OPEN3D_MESH_OBJ, 
    DATA_OPEN3D_MESH_PLY, 
    DATA_OPENMVS_DENSE_PLY, 
    DEFAULT_SCAN_MODE
)
class Open3dManager:
    """
    Classe per la gestione delle varie fasi dell'esecuzione di Open3D.
    """
    def __init__(
            self, 
            scan_mode: Literal['indoor', 'outdoor'] = DEFAULT_SCAN_MODE,
            dense_ply_path: Path = DATA_OPENMVS_DENSE_PLY,
            mesh_ply_path: Path = DATA_OPEN3D_MESH_PLY,
            mesh_obj_path: Path = DATA_OPEN3D_MESH_OBJ,
            scale_real_distance: float = 1
        ):
        self.scan_mode = scan_mode
        self.dense_ply_path = dense_ply_path
        self.mesh_ply_path = mesh_ply_path
        self.mesh_obj_path = mesh_obj_path
        self.mesh = None
        self.dense = None
        self.scale_real_distance = scale_real_distance
        o3d.utility.set_verbosity_level(o3d.utility.VerbosityLevel.Error)

    def start_full_open3d_pipeline(self):
        """
        funzione che gestisce la pipeline di Open3D.
        """
        self.run_dense_importer() # 1
        self.run_auto_alignement() # 2
        self.run_geometry_estimater() # 3
        self.run_fog_remover() # 4
        self.run_poisson_mesher() # 5
        self.run_noise_remover() # 6
        self.run_smoothing() # 7
        self.run_topological_cleaning() # 8
        # if self.scan_mode == 'indoor': self.generate_scaled_mesh(scale_real_distance)
        self.run_exporter() # 9
        self.run_viewer() # 10

    def generate_scaled_mesh(self):
        """
        Funzione usata in indoor mode per dare una dimensione reale agli oggetti.
        """
        if not self.mesh:
            raise Open3dError('Mesh not found.')
        
        if self.scan_mode != 'indoor':
            raise Open3dError('Scan mode error')
        
        virtual_distance = self._get_virtual_distance()
        
        scale_factor = self._get_scale_factor(self.scale_real_distance, virtual_distance)

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



    # ristrutturazione codice 

    def run_mesh_importer(self):
        """
        Funzione per importare una mesh gia esistente.
        """
        try:
            self.mesh = o3d.io.read_triangle_mesh(
                str(self.mesh_ply_path), 
                enable_post_processing=True
            )   
            success_alert('Mesh imported.')
        except Exception:
            raise Open3dError('Import failed.')

    def run_dense_importer(self):
        """
        Funzione per caricare la dense per la generazione della mesh.
        """
        if not self.dense_ply_path.exists():
            raise Open3dError(f"File {self.dense_ply_path.name} not found.")
            
        try:
            self.dense = o3d.io.read_point_cloud(str(self.dense_ply_path))
            success_alert('Dense imported.')
        except Exception:
            raise Open3dError('Import failed.')

    def run_auto_alignement(self):
        """
        Funzione che raddrizza il modello.
        """
        if self.dense is None:
            raise Open3dError(f"Dense not found.")
        
        try:
            plane_model, inliers = self.dense.segment_plane(distance_threshold=0.02, ransac_n=3, num_iterations=1000)
            [a, b, c, d] = plane_model
            normal = np.array([a, b, c])
            
            z_axis = np.array([0, 0, 1])
            if c < 0: normal = -normal 
            
            v = np.cross(normal, z_axis)
            s = np.linalg.norm(v)
            c_val = np.dot(normal, z_axis)
            
            if s > 1e-6:
                vx = np.array([[0, -v[2], v[1]], [v[2], 0, -v[0]], [-v[1], v[0], 0]])
                R = np.eye(3) + vx + np.dot(vx, vx) * ((1 - c_val) / (s**2))
                self.dense.rotate(R, center=(0, 0, 0))
            
            z_mean = np.mean(np.asarray(self.dense.points)[inliers][:, 2])
            self.dense.translate((0, 0, -z_mean))
            success_alert('Alignement completed.')
        except Exception:
            raise Open3dError('Alignement failed.')

    def run_geometry_estimater(self):
        """
        Funzione per il calcolo delle normali.
        """
        if self.dense is None:
            raise Open3dError(f"Dense not found.")
        
        try:
            self.dense.estimate_normals(search_param=o3d.geometry.KDTreeSearchParamHybrid(radius=0.05, max_nn=20)) # si puo modificare con delle var
            self.dense.orient_normals_towards_camera_location(camera_location=np.array([0, 0, 0]))
            self.dense.orient_normals_consistent_tangent_plane(10)
            success_alert('Geometry estimated.')
        except Exception:
            raise Open3dError('Geometry estimation failed.')
        
    def run_fog_remover(self):
        """
        Funzione per rimuovere la nebbia dalla nuvola.
        """
        if self.dense is None:
            raise Open3dError(f"Dense not found.")
        
        try:
            _, index = self.dense.remove_statistical_outlier(nb_neighbors=20, std_ratio=2.0) # si puo modificare con delle var
            self.dense = self.dense.select_by_index(index)
            success_alert('Fog removed.')
        except Exception:
            raise Open3dError('fog removal failed.')
        
    def run_poisson_mesher(self):
        """
        Funzione che tramite l'algoritmo di poisson genera la mesh.
        """
        if self.dense is None:
            raise Open3dError(f"Dense not found.")

        try:
            self.mesh, densities = o3d.geometry.TriangleMesh.create_from_point_cloud_poisson(self.dense, depth=9)

            densities = np.asarray(densities)
            vertices_to_remove = densities < np.quantile(densities, 0.05)
            self.mesh.remove_vertices_by_mask(vertices_to_remove)

            self.dense_ply_path.parent.mkdir(parents=True, exist_ok=True)
            o3d.io.write_triangle_mesh(str(self.mesh_ply_path), self.mesh)
            success_alert(f'Mesh reconstructed.')
        except Exception:
            raise Open3dError('Mesh reconstruction failed.')
    
    def run_noise_remover(self):
        """
        Funzione per rimuovere il rumore.
        """
        if self.mesh is None:
            raise Open3dError(f"Mesh not found.")
        
        try:
            triangle_clusters, cluster_n_triangles, _ = self.mesh.cluster_connected_triangles()
            triangle_clusters = np.asarray(triangle_clusters)
            cluster_n_triangles = np.asarray(cluster_n_triangles)

            if len(cluster_n_triangles) > 1:
                largest_cluster_idx = cluster_n_triangles.argmax()
                triangles_to_remove = triangle_clusters != largest_cluster_idx
                self.mesh.remove_triangles_by_mask(triangles_to_remove)
                self.mesh.remove_unreferenced_vertices()
                n_rimossi = len(cluster_n_triangles) - 1
                success_alert(f'{n_rimossi} clusters removed.')
            else:
                success_alert('No clusters removed.')
        except Exception:
            raise Open3dError('Clusters removal failed.')

    def run_smoothing(self):
        """
        Funzione che pulisce gli spigoli.
        """
        if self.mesh is None:
            raise Open3dError(f"Mesh not found.")

        try:
            self.mesh = self.mesh.filter_smooth_taubin(number_of_iterations=2) # si puo modificare con delle var
            success_alert('Smoothing completed.')
        except Exception:
            raise Open3dError('Smoothing failed.')

    def run_topological_cleaning(self):
        """
        Funzione per la pulizia topologica.
        """
        if self.mesh is None:
            raise Open3dError(f"Mesh not found.")
        
        try:
            self.mesh.remove_degenerate_triangles()
            self.mesh.remove_duplicated_triangles()
            self.mesh.remove_duplicated_vertices()
            self.mesh.remove_unreferenced_vertices()
            success_alert('Topological cleaning completed.')
        except Exception:
            raise Open3dError('Topological cleaning failed.')

    def run_scaler(self):
        pass

    # TODO: esportare anche i file delle texture
    def run_exporter(self):
        """
        Funzione per esportare la mesh in un file .obj.
        """
        if self.mesh is None:
            raise Open3dError(f"Mesh not found.")
        
        self.mesh_obj_path.parent.mkdir(parents=True, exist_ok=True)

        try:
            o3d.io.write_triangle_mesh(str(self.mesh_obj_path), self.mesh, write_ascii=False)
            success_alert('Exportation completed.')
        except Exception:
            raise Open3dError('Exportation failed.')

    def run_viewer(self):
        """
        Funzione per visualizzare la mesh.
        """
        if self.mesh is None:
            raise Open3dError(f"Mesh not found.")
        
        try:
            o3d.visualization.draw_geometries(
                [self.mesh], 
                window_name="Open3D - Visualizzatore Modello",
                width=1024, 
                height=768,
                mesh_show_wireframe=False,
                mesh_show_back_face=True
            )
            success_alert('Visualization completed.')
        except Exception:
            raise Open3dError('Visualization failed.')
        
