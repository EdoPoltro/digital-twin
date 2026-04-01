# Digital twin

<span style="color:red">
       Rinominare il progetto o scegliere il nome definitivo.
</span>

## Description

L'applicazione è in grado di elaborare una serie di immagini, processarle e tramite COLMAP, OpenMVS e Open3D di generare una nuvola sparsa, una nuvola densa e una mesh texturizzata.

L'applicazione inoltre riesce a gestire due modailta di scan (indoor e outdoor) per la mappatura di aree molto piccole, come ambienti domestici e aree relativamente grandi come case o strutture. a seconda della modalita di scan viene avviata una pipeline dedicata.

E' possibile anche tramite il modello 3D fare misurazioni, croppare la mesh, unire due mesh ed esportare il modello su autocad.

## Environment setup windows

Il progetto e scritto interamente in [Python 3.11.9](https://www.python.org/ftp/python/3.11.9/python-3.11.9-amd64.exe) e utilizza come moteri di calcolo per la generazione delle nuvole di punti [Colmap 4.0.2](https://github.com/colmap/colmap/releases/download/4.0.2/colmap-x64-windows-cuda.zip) e [OpenMVS 2.4](https://github.com/cdcseacave/openMVS/releases/download/v2.4.0/OpenMVS_Windows_x64.zip).

<span style="color:red">
       mettere link sia per cuda che non
</span>

Per preparare l'ambiente all'esecuzione di Digital twin è necessario seguire queste istruzioni:

<span style="color:red">
       dire che ce distinzione tra colmap cuda e no e ancehe per openmvs
</span>

- Verificare di disporre di una scheda video NVIDIA con i driver aggiornati all'ultima versione.

- Tramite github scaricare la cartella del progetto `git clone https://github.com/EdoPoltro/progetto-digital-twin.git`.

- Scaricare Colmap 4.0.2 da github, estrarre la cartella contenente i file .exe, rinominarla come "colmap" e inserirla nella cartella /digital_twin/engines all'interno del progetto.

- Scaricare OpenMVS 2.4 da github, estrarre la cartella contenente i file .exe, rinominarla "openmvs" e inserirla nella cartella /digital_twin/engines all'interno del progetto.

- Generare la venv: `py -3.11 -m venv venv`.

- Avviare la venv: `.\venv\Scripts\activate`.

- Se la poweshell da problemi lanciare `Set-ExecutionPolicy -ExecutionPolicy RemoteSigned -Scope CurrentUser`.

- Installare le dipendenze dal file requiremnts.txt: `pip install -r requirements.txt`.

- Eseguire la venv su main.py: `python main.py` o `.\venv\Scripts\python.exe main.py`.

## Environment setup linux

<span style="color:red">
Durante lo sviluppo è stato necessario passare ad una macchina virtuale Vast AI per aumentare le prestazioni di calcolo ed il setup è leggermente piu complicati di quello su windows:

- Tramite github scaricare la cartella del progetto `git clone https://github.com/EdoPoltro/progetto-digital-twin.git`.

- Scaricare da github la versione per Ubuntu di OpenMVS 2.4, estrarre la cartella contenente i file .exe, rinominarla "openmvs" e inserirla nella cartella /digital_twin/engines all'interno del progetto.

- Dare i permessi ai file al suo interno `chmod +x /workspace/progetto-digital-twin/engines/openmvs/*`.

- Scaricare tramite conda una venv per COLMAP.

- Attivare le due venv

</span>

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

Se il programma è in mpdalita indoor allora effettuerà con open3d la fase di scaling, se il programma è in outdoor mode il programma effettuerà le fasi di GPS metadata uploading.

```
| Ingestion | -- > | Processing | -- > ( Metadata uploading ) --
                                                                |
                                                                |
 ------- | Undistorting | < -- | Aligning | < -- | Sparse | < --
|
|
 -- > | Dense | --> | Mesh | -- > | Noise removing | -----------
                                                                |
                                                                |
       | Visualization | < -- | Texturing | < -- ( Scaling ) <--
```
Una volta caricate le immagini scattate nella cartella /digital_twin/data/processing/raw il programma seguirà la pipeline associata alla modalita di scan e otterrà una mesh visualizzabile da open3d.

In fase di sviluppo ho notato che ci sono 2 pipeline possibili per la generazione della mesh texturizzata:

### Processing

In questa fase Creo un array di CapturedImage dove salvo tutti i dati EXIF generali delle foto ed effettuo i relativi controlli. Nella fase di estrazione dei dati è stato necessario fare uno studio per capire quali fossero essenziali e quali no: i dati gps come altitudine, latitudine e longitudine diventano necessari qualora la modalità di scan sia 'outdoor' per usufruire della georeferenzazione, mentre i dati delle camere come la focale e la risoluzione sono sempre obbligatori e vengono usati proprio per la generazione della nuvola di punti.

Dopo la prima selezione le foto passano alla fase di processamento vera e propria dove è possibile configurare il processor manager in due modalità: default e underwater, a seconda della modalità scelta la pipeline di filtri che vengono applicati cambia.

Per gestire lo stato delle immagini ed il loro path è stato implmentato un promoter che ha il copito di spostare le foto, aggiornare lo stato ed il path. Tutto questo per separare la fase di processamento da quella di gestione delle cartelle durante la pipeline. 
Alla fine della fase di processing le foto hanno stato processed e si trovano nella relativa cartella pronte ad essere usate.

```
| Raw | -- > | Ingestion | -- > | Extraction | -- > | Processor | -- > | Processed |
```

### COLMAP 

COLMAP è un motore di calcolo scritto in C ottimo per la generazione di nuvole di punti sparse ricevendo in input delle immagini. In questa fase appunto vanno predisposti i dati per essere passati successivamente a COLMAP, per essere elaborati e successivamente esportati nel formato corretto per la fase successiva.

Il file metadata uploader si occupa di generare un db sqllight con i dati delle telecamere e un file txt con i dati gps delle foto. Nelle nuove versioni di COLMAP (>=4.0) prende automaticamente i dati delle camere dalle foto senza passargli un database. 

Successivamente viene avviata la pipeline di colmap che genera la nuvola sparsa, successivamente a seconda della modalità di scan adotta l'aligner corretto per migliorare gli assi e la posizione dei punti e prepara le immagini per il passo successivo rimuovendo la distorsione dovuta dalla lente della camera.

<span style="color:red">COLMAP può generare una nuvola di punti densa ma per ora non ho provato, dovrebbe essere peggiore in prestazioni ma va verificato.</span>

```
| metadata uploading | -- > | sparse | -- > | aligned | -- > | undisotrted |
```

### OpenMVS

### Open3D

## Shooting & Asset Acquisition

## System Requirements & Performance

