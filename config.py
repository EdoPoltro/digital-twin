from pathlib import Path

BASE_DIR = Path(__file__).resolve().parent

DATA_DIR = BASE_DIR / 'data'
INPUT_DIR = DATA_DIR / 'input'
INPUT_RAW_IMAGES_DIR = INPUT_DIR / 'raw_images'
OUTPUT_DIR = DATA_DIR / 'output'

SUPPORTED_INPUT_FORMATS = ('.jpg', '.jpeg', '.png', '.tiff', '.tif')
DEFAULT_PROCESSED_OUTPUT_FORMAT = '.png'
SUPPORTED_3D_FORMATS = ('.ply', '.obj', '.stl')
