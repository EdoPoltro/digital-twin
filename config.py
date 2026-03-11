from pathlib import Path

BASE_DIR = Path(__file__).resolve().parent
COLMAP_EXE = Path("C:/Users/EdoXP/Desktop/COLMAP/bin/colmap.exe")

DATA_DIR = BASE_DIR / 'data'
MODELS_DIR = BASE_DIR / 'models'
UTILS_DIR = BASE_DIR / 'utils'
SRC_DIR = BASE_DIR / 'src'

RAW_IMAGES_DIR = DATA_DIR / 'raw'
INTERIM_IMAGES_DIR = DATA_DIR / 'interim'
PROCESSED_IMAGES_DIR = DATA_DIR / 'processed'
COLMAP_DIR = DATA_DIR / 'colmap'
COLMAP_SPARSE_DIR = COLMAP_DIR / 'sparse'
COLMAP_DENSE_DIR = COLMAP_DIR /  'dense'
OUTPUT_3D_MODELS_DIR = DATA_DIR / '3d_outputs'

SUPPORTED_INPUT_FORMATS = ('.jpg', '.jpeg', '.png', '.tiff', '.tif')
DEFAULT_PROCESSED_OUTPUT_FORMAT = '.png'
SUPPORTED_3D_FORMATS = ('.ply', '.obj', '.stl')

DEFAULT_ENVIRONMENT_CLEAN_UP = [INTERIM_IMAGES_DIR, PROCESSED_IMAGES_DIR, OUTPUT_3D_MODELS_DIR, COLMAP_DIR]
