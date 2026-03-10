from models.image_data import CapturedImage
from src.ingestion import get_raw_captured_images
from src.metadata_extractor import extract_all_raw_captured_images_metadata
from utils.exceptions import BaseError

def main():
    print("="*40)
    print('Digital Twin 3D - Avvio pipline')
    print("="*40)

    try:
        print('Creazione dell\'array di immagini')
        captured_images: list[CapturedImage] = get_raw_captured_images()

        print('Estrazione dei metadati')
        captured_images = extract_all_raw_captured_images_metadata(captured_images)

# print per debug
        foto_test = captured_images[0]

        print("\n" + "="*40)
        print("📸 REPORT PRIMA IMMAGINE")
        print("="*40)
        print(f"File:        {foto_test.file_name}")
        print(f"Risoluzione: {foto_test.camera_metadata.resolution} pixel")
        
        # Gestiamo il caso in cui la foto non abbia marca/modello
        marca = foto_test.camera_metadata.make or "Sconosciuta"
        modello = foto_test.camera_metadata.model or "Sconosciuto"
        focale = foto_test.camera_metadata.focal_length or "N/D"
        
        print(f"Fotocamera:  {marca} {modello}")
        print(f"Focale:      {focale} mm")
        print(f"Sensore:     {foto_test.camera_metadata.sensor_size}")
        
        # --- NUOVA SEZIONE: SPATIAL METADATA ---
        print("-" * 40)
        
        # Gestiamo il caso in cui i dati GPS siano None
        lat = foto_test.spatial_metadata.latitude
        lon = foto_test.spatial_metadata.longitude
        alt = foto_test.spatial_metadata.altitude
        
        # Formattiamo i numeri se esistono, altrimenti scriviamo "N/D"
        lat_str = f"{lat:.6f}°" if lat is not None else "N/D"
        lon_str = f"{lon:.6f}°" if lon is not None else "N/D"
        alt_str = f"{alt:.2f} m" if alt is not None else "N/D"
        date = str(foto_test.spatial_metadata.timestamp)
        
        print(f"Latitudine:  {lat_str}")
        print(f"Longitudine: {lon_str}")
        print(f"Altitudine:  {alt_str}")
        print(f"Timestamp:  {date}")
        print("="*40 + "\n")
        
    except BaseError as e:
        print(e)

    except Exception as e:
        print(f'Errore critico di sistema: {e}')

if __name__ == "__main__":
    main()