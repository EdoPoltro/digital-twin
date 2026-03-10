import json
from pathlib import Path
from utils.exceptions import FileAccessError, FileNotFoundError

def open_json(file_path: Path) -> dict:
    """
    Legge un file JSON dal disco e restituisce un dizionario.

    Args:
        file_path (Path): percorso del file

    Raises:
        FileNotFoundError
        FileAccessError

    Returns:
        dict
    """
    if not file_path.exists():
        raise FileNotFoundError(file_path)
    try:
        with open(file_path, "r", encoding="utf-8") as file:
            return json.load(file)
    except (json.JSONDecodeError, PermissionError) as e:
        raise FileAccessError(file_path, e)