import json
from pathlib import Path
from config import DEFAULT_ENVIRONMENT_CLEAN_UP
from src.core.exceptions import EnvSetupError, UtilsError
import shutil
import sqlite3
from pathlib import Path

from src.utils.log_utils import success_alert, warning_alert

def open_json(file_path: Path) -> dict:
    """
    Legge un file JSON dal disco e restituisce un dizionario.

    Args:
        file_path (Path): percorso del file

    Raises:
        UtilsError

    Returns:
        dict
    """
    if not file_path.exists():
        raise UtilsError(f'File not found: {file_path}')
    try:
        with open(file_path, "r", encoding="utf-8") as file:
            return json.load(file)
    except (json.JSONDecodeError, PermissionError) as e:
        raise UtilsError(f'Access denied: {file_path}')
    
def setup_project_environment(directories: list[Path] = DEFAULT_ENVIRONMENT_CLEAN_UP):
    """
    Funzione per la pulizia delle cartelle dei risultati lungo la pipeline.
    """
    for dir in directories:
        if dir.exists():
            try:
                shutil.rmtree(dir)
                dir.mkdir(parents=True, exist_ok=True)
            except Exception:
                raise EnvSetupError(f'Failed to clean up folder {dir}.')
        else:
            dir.mkdir(parents=True, exist_ok=True)
    success_alert('Project initialized.')


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

def folders_counter(path: Path) -> int:
    """
    Funzione per contare quante sottocartelle ha la cartella al percorso path.

    Args:
        path (Path): cartella di input

    Raises:
        UtilsError

    Returns:
        int
    """
    if not path.exists():
        raise UtilsError('Folder not found.')
    
    folders = len([f for f in path.iterdir() if f.is_dir()])
    
    return folders