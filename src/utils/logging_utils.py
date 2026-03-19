# ALERT COLORS

CLR_RESET = "\033[0m"    
CLR_WARNING = "\033[93m"  
CLR_ERROR = "\033[91m"    

def warning_alert(msg: str):
    print(f'{CLR_WARNING}[WARNING]: {msg}{CLR_RESET}')

def error_alert(msg: str):
    print(f'{CLR_ERROR}[ERORR]: {msg}{CLR_RESET}')

def log_alert(msg: str):
    print(f'{CLR_RESET}[✅ ]: {msg}{CLR_RESET}')
