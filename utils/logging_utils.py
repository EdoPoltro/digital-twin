from config import CLR_ERROR, CLR_RESET, CLR_WARNING

def warning_alert(msg: str):
    print(f'{CLR_WARNING}[WARNING]: {msg}{CLR_RESET}')

def error_alert(msg: str):
    print(f'{CLR_ERROR}[ERORR]: {msg}{CLR_RESET}')