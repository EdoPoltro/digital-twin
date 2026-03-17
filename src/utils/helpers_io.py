import json
from pathlib import Path
from src.core.exceptions import EnvSetupError, FileAccessError, FileNotFoundError
import shutil
import sqlite3
from pathlib import Path

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
    
def setup_project_environment(directories: list[Path]):
    for dir in directories:
        if dir.exists():
            try:
                shutil.rmtree(dir)
                dir.mkdir(parents=True, exist_ok=True)
            except OSError as e:
                raise EnvSetupError(str(dir))
        else:
            dir.mkdir(parents=True, exist_ok=True)


def write_text_to_file(file_path: Path, content: str):
    """
    Funzione che scrive su un file dato il suo percosrso e che lo crea se non esiste

    Args
        path (Path)
        content (str)
    """
    file_path.parent.mkdir(parents=True, exist_ok=True)
    with open(file_path, 'w', encoding='utf-8') as f:
        f.write(content)

def init_sqlite_connection(db_path: Path) -> sqlite3.Connection:
    """
    Prepara il file sul disco e restituisce la connessione al database.

    Args:
        db_path (Path)

    Returns:
        sqlite3.Connection
    """
    db_path.parent.mkdir(parents=True, exist_ok=True)
    if db_path.exists():
        db_path.unlink()
    
    return sqlite3.connect(db_path)