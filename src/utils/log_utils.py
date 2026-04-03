import itertools
import multiprocessing
import subprocess
import sys
import threading
import time
from tqdm import tqdm
from typing import Iterable, Any
import itertools

from config import IS_WINDOWS

# ALERT COLORS

CLR_RESET = "\033[0m"    
CLR_WARNING = "\033[93m"  
CLR_ERROR = "\033[91m"    
DEFAULT_LOADING_MESSAGGE = "Process in progress."

def warning_alert(msg: str):
    print(f'{CLR_WARNING}[WARNING]: {msg.capitalize()}{CLR_RESET}')

def error_alert(msg: str):
    print(f'{CLR_ERROR}[ERROR]: {msg.capitalize()}{CLR_RESET}')

def success_alert(msg: str):
    print(f'{CLR_RESET}[SUCCESS]: {msg.capitalize()}{CLR_RESET}')

# successivamente si può ampliare con la percentuale di progresso ma dipende molto dall'output del mio motore di calcolo.
def subprocess_execution(command: list[str], loading_msg: str = DEFAULT_LOADING_MESSAGGE, output_log: bool = False, check: bool = True, **kwargs):

    timeout = kwargs.pop('timeout', None)
    
    if not output_log:
        if 'stdout' not in kwargs:
            kwargs['stdout'] = subprocess.DEVNULL
        if 'stderr' not in kwargs:
            kwargs['stderr'] = subprocess.DEVNULL
        if IS_WINDOWS and 'creationflags' not in kwargs:
            kwargs['creationflags'] = 0x08000000

    process = subprocess.Popen(command, **kwargs)

    start_time = time.time()

    try:
        if output_log:
            print(f"\n[LOG]: {loading_msg.capitalize()}\n{'-'*50}")
            try:
                process.wait(timeout=timeout)
            except subprocess.TimeoutExpired:
                process.kill()
                raise
            print(f"{'-'*50}\n")
        else:
            spinner = itertools.cycle(['⠋', '⠙', '⠹', '⠸', '⠼', '⠴', '⠦', '⠧', '⠇', '⠏'])
            while process.poll() is None:
                if timeout is not None and (time.time() - start_time) > timeout:
                    process.kill()
                    sys.stdout.write('\r' + ' ' * (len(loading_msg) + 5) + '\r')
                    raise subprocess.TimeoutExpired(process.args, timeout)
                
                sys.stdout.write(f'\r{next(spinner)} {loading_msg}')
                sys.stdout.flush()
                time.sleep(0.1)

            sys.stdout.write('\r' + ' ' * (len(loading_msg) + 5) + '\r')
            sys.stdout.flush()

        if check and process.returncode != 0:
            raise subprocess.CalledProcessError(process.returncode, command)
            
    except KeyboardInterrupt:
        process.kill()
        sys.stdout.write('\r' + ' ' * (len(loading_msg) + 5) + '\r')
        sys.stdout.flush()
        error_alert('Process interrupted by user.')
        raise

def progress_bar(iterable: Iterable[Any], description: str = DEFAULT_LOADING_MESSAGGE, total: int = None):
    """
    Funzione per monitorare il processamento di liste di oggetti
    """
    return tqdm(
        iterable, 
        desc=str(description), 
        bar_format="{l_bar}{bar}| {n_fmt}/{total_fmt} [{elapsed}<{remaining}, {rate_fmt}]",
        dynamic_ncols=True,
        leave=False,
        total=total
    )

class Loader:
    def __init__(self, end_msg="Done!"):
        self.end_msg = end_msg
        self.desc = ""
        self._process = None

    @staticmethod
    def _animate(desc, stop_event):
        """Funzione statica che gira in un processo separato."""
        spinner = itertools.cycle(['⠋', '⠙', '⠹', '⠸', '⠼', '⠴', '⠦', '⠧', '⠇', '⠏'])
        try:
            while not stop_event.is_set():
                sys.stdout.write(f'\r{next(spinner)} {desc}')
                sys.stdout.flush()
                time.sleep(0.1)
        finally:
            # Pulisce la riga prima di chiudere il processo
            sys.stdout.write('\r' + ' ' * (len(desc) + 20) + '\r')
            sys.stdout.flush()

    def start(self, desc=DEFAULT_LOADING_MESSAGGE):
        """Avvia lo spinner in un processo indipendente."""
        self.desc = desc
        self._stop_event = multiprocessing.Event()
        self._process = multiprocessing.Process(
            target=self._animate, 
            args=(self.desc, self._stop_event),
            daemon=True # Muore se il main process viene killato
        )
        self._process.start()
        return self

    def stop(self):
        """Ferma il processo dello spinner."""
        if self._process and self._process.is_alive():
            self._stop_event.set()
            self._process.join(timeout=0.5)
            if self._process.is_alive():
                self._process.terminate()