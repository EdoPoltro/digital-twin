import itertools
import subprocess
import sys
import time

# ALERT COLORS

CLR_RESET = "\033[0m"    
CLR_WARNING = "\033[93m"  
CLR_ERROR = "\033[91m"    
DEFAULT_LOADING_MESSAGGE = "Process in progress."

def warning_alert(msg: str):
    print(f'{CLR_WARNING}[WARNING]: {msg}{CLR_RESET}')

def error_alert(msg: str):
    print(f'{CLR_ERROR}[ERROR]: {msg}{CLR_RESET}')

def success_alert(msg: str):
    print(f'{CLR_RESET}[SUCCESS]: {msg}{CLR_RESET}')

# successivamente si può ampliare con la percentuale di progresso ma dipende molto dall'output del mio motore di calcolo.
def subprocess_execution(command: list[str], loading_msg: str = DEFAULT_LOADING_MESSAGGE, output_log: bool = False, check: bool = True, **kwargs):

    timeout = kwargs.pop('timeout', None)

    
    if not output_log:
        if 'stdout' not in kwargs:
            kwargs['stdout'] = subprocess.DEVNULL
        if 'stderr' not in kwargs:
            kwargs['stderr'] = subprocess.DEVNULL
        if 'creationflags' not in kwargs:
            kwargs['creationflags'] = subprocess.CREATE_NO_WINDOW

    process = subprocess.Popen(command, **kwargs)

    start_time = time.time()

    try:
        if output_log:
            print(f"\n⚙️ [RUNNING]: {loading_msg}\n{'-'*50}")
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
