# libreria per calcoli

def exif_gps_to_decimal(exif_gps: tuple) -> float:
    """
    Funzione che accetta i dati exif del gps in tuple e li traduce in decimali.

    Args:
        exif_gps (tuple): tupla di longitudine o latitudine in formato exif

    Returns:
        float

    Raises:
        ValueError
        TypeError
        IndexError
    """
    d = float(exif_gps[0])
    m = float(exif_gps[1])
    s = float(exif_gps[2])
    return d + ( m / 60.0 ) + ( s / 3600.0 )
