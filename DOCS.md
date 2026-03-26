# Digital twin

## Description

## Environment setup windows

Il progetto e scritto interamente in [Python 3.11.9](https://www.python.org/ftp/python/3.11.9/python-3.11.9-amd64.exe) e utilizza come moteri di calcolo per la generazione delle nuvole di punti [Colmap 4.0.2](https://github.com/colmap/colmap/releases/download/4.0.2/colmap-x64-windows-cuda.zip) e [OpenMVS 2.4](https://github.com/cdcseacave/openMVS/releases/download/v2.4.0/OpenMVS_Windows_x64.zip).

Per preparare l'ambiente all'esecuzione di Digital twin è necessario seguire queste istruzioni:

- Verificare di disporre di una scheda video NVIDIA con i driver aggiornati all'ultima versione.

- Scaricare Colmap 4.0.2 da github, estrarre la cartella contenente i file .exe, rinominarla come "colmap" e inserirla nella cartella /digital_twin/engines all'interno del progetto.

- Scaricare OpenMVS 2.4 da github, estrarre la cartella contenente i file .exe, rinominarla "openmvs" e inserirla nella cartella /digital_twin/engines all'interno del progetto.

- Generare la venv: `py -3.11 -m venv venv`.

- Avviare la venv: `.\venv\Scripts\activate`.

- Installare le dipendenze dal file requiremnts.txt: `pip install -r requirements.txt`.

- Eseguire la venv su main.py: `python main.py` o `.\venv\Scripts\python.exe main.py`. 

## Project structure

```
digital_twin
|_ data
|   |_ processing
|   |   |_ raw  < ---- input image
|   |   |_ processed
|   |_ colmap
|   |_ openmvs
|   |_ open3d  < ---- result mesh
|_ src
|   |_ processing
|   |   |_ ingestion.py
|   |   |_ metadata_extractor.py
|   |   |_ processor_manager.py
|   |   |_ promoter.py
|   |_ colmap
|   |   |_ colmap_manager.py
|   |   |_ metadata_uploader.py
|   |_ openmvs
|   |   |_ openmvs_manager.py
|   |_ open3d
|   |   |_ open3d_manager.py
|   |_ models
|   |_ core
|   |   |_ exceptions.py
|   |   |_ pipeline.py
|   |_ utils
|   |   |_ io_utils.py
|   |   |_ log_utils.py
|   |   |_ math_utils.py
|_ engines
|   |_ colmap
|   |_ openmvs
|_ main.py  < ---- entry point
|_ config.py
|_ requrements.txt
```

## Pipeline
La pipeline viene leggermente modificata a secodna della dimensione dello scan: è presente una variabile d'ambiente nel file config.py chiamata SCAN_MODE: 'indoor' | 'outdoor' che gestisce la dimensione dello scan.

Se il programma è in mpdalita indoor allora effettuerà con open3d la fase di scaling, se il programma è in outdoor mode il programma effettuerà le fasi di metadata uploading e aligneing, non si possono effettuare la fase di scaling e aligneing nella stessa pipeline perchè sono specifiche per il tipo di scan.

```
| Ingestion | -- > | Processing | -- > ( Metadata uploading ) --
                                                                |
                                                                |
 ------- | Undistorting | < -- ( Aligning ) < -- | Sparse | < --
|
|
 -- > | Dense | --> | Mesh | -- > | Noise removing | -----------
                                                                |
                                                                |
       | Visualization | < -- | Texturing | < -- ( Scaling ) <--
```
Una volta caricate le immagini scattate nella cartella /digital_twin/data/processing/raw il programma seguirà la pipeline associata alla modalita di scan e otterrà una mesh visualizzabile da open3d.

In fase di sviluppo ho notato che ci sono 2 pipeline possibili per la generazione della mesh texturizzata:



## Shooting & Asset Acquisition

## System Requirements & Performance

