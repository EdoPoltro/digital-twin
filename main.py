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
        raw_captured_images: list[CapturedImage] = get_raw_captured_images()

        print('Estrazione dei metadati')
        extract_all_raw_captured_images_metadata(raw_captured_images)

        # print per debug

        foto_test = raw_captured_images[2]

        print("\n" + "="*40)
        print("📸 REPORT PRIMA IMMAGINE")
        print("="*40)
        print(f"File:        {foto_test.file_name}")
        print(f"Risoluzione: {foto_test.camera_metadata.resolution} pixel")
        
        # Gestiamo il caso in cui la foto non abbia marca/modello (es. foto scaricate da WhatsApp)
        marca = foto_test.camera_metadata.make or "Sconosciuta"
        modello = foto_test.camera_metadata.model or "Sconosciuto"
        focale = foto_test.camera_metadata.focal_length or "N/D"
        
        print(f"Fotocamera:  {marca} {modello}")
        print(f"Focale:      {focale} mm")
        print(f"Sensore:     {foto_test.camera_metadata.sensor_size} (Da calcolare in futuro)")
        print("="*40 + "\n")

        # print per debug
        
    except BaseError as e:
        print(e)

    except Exception as e:
        print(f'Errore critico di sistema: {e}')

if __name__ == "__main__":
    main()