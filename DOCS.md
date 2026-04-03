# Digital twin

<span style="color:red">
       Rinominare il progetto o scegliere il nome definitivo.
</span>

## Description

L'applicazione è in grado di elaborare una serie di immagini, processarle e tramite COLMAP, OpenMVS e Open3D di generare una nuvola sparsa, una nuvola densa e una mesh texturizzata.

L'applicazione inoltre riesce a gestire due modailta di scan (indoor e outdoor) per la mappatura di aree molto piccole, come ambienti domestici e aree relativamente grandi come case o strutture. a seconda della modalita di scan viene avviata una pipeline dedicata.

E' possibile anche tramite il modello 3D fare misurazioni, croppare la mesh, unire due mesh ed esportare il modello su autocad.

## Environment setup windows

Il progetto e scritto interamente in [Python 3.11.9](https://www.python.org/ftp/python/3.11.9/python-3.11.9-amd64.exe) e utilizza come motori di calcolo per la generazione delle nuvole di punti [Colmap 4.0.2](https://github.com/colmap/colmap) e [OpenMVS 2.4](https://github.com/cdcseacave/openMVS).

Downloads:

- [COLMAP 4.0.2 WINDOWS CUDA](https://github.com/colmap/colmap/releases/download/4.0.2/colmap-x64-windows-cuda.zip) (si può disabilitare)
- [COLMAP 4.0.2 WINDOWS NO CUDA](https://github.com/colmap/colmap/releases/download/4.0.2/colmap-x64-windows-nocuda.zip)

- [OpenMVS 2.4 WINDOWS CUDA](https://github.com/cdcseacave/openMVS/releases/download/v2.4.0/OpenMVS_Windows_x64_CUDA.7z)
- [OpenMVS 2.4 WINDOWS NO CUDA](https://github.com/cdcseacave/openMVS/releases/download/v2.4.0/OpenMVS_Windows_x64.zip)
- [OpenMVS 2.4 LINUX](https://github.com/cdcseacave/openMVS/releases/download/v2.4.0/OpenMVS_Ubuntu_x64.zip)

Per preparare l'ambiente all'esecuzione di Digital twin è necessario seguire queste istruzioni:

- Per utilizare le versioni cuda dei motori di calcolo verificare di disporre di una scheda video NVIDIA con i driver aggiornati all'ultima versione.

- Tramite github scaricare la cartella del progetto `git clone https://github.com/EdoPoltro/progetto-digital-twin.git`.

- Scaricare Colmap 4.0.2 da github, estrarre la cartella contenente i file .exe, rinominarla come "colmap" e inserirla nella cartella `progetto-digital-twin.git/engines` all'interno del progetto.

- Scaricare OpenMVS 2.4 da github, estrarre la cartella contenente i file .exe, rinominarla "openmvs" e inserirla nella cartella `progetto-digital-twin.git/engines` all'interno del progetto.

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
|   |   |_ video
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

Per popolare il progetto di immagini sono previste due strategie possibili: caricando in manualmente `data/processing/raw` le immagini o inserendo un video in `data/processing/video` e segnalando il metodo utilizzato nel file config.py come extraction_mode.
Un manager dedicato si occupa di catturare i frame del video per ogni intervallo di 0.5s (regolabile tramite il file delle config.py), di filtrarli per tenere solo le foto utilizzabili e di caricarali in `data/processing/raw` per proseguire con la pipeline. Questa aggiunta ha permesso di ottenere molte più foto con molto meno sforzo e questo a portato un incremento nelle prestazioni della nuvola sparsa.

Successivamente viene creato un array di CapturedImage dove posso salvare tutti i dati EXIF generali delle foto ed effettuo i relativi controlli. 
Nella fase di estrazione dei dati è stato necessario fare uno studio per capire quali fossero essenziali e quali no: i dati gps come altitudine, latitudine e longitudine diventano necessari qualora la modalità di scan sia 'outdoor' per usufruire della georeferenzazione, mentre i dati delle camere come la focale e la risoluzione sono sempre obbligatori e vengono usati proprio per la generazione della nuvola di punti.

Nelle versioni più aggiornate di COLMAP (come 4.0.2) non e più necessario estrarre manualmente i dati delle camere per poi passarli all'interfaccia che si occuperà di estrarli autonomamente. 

Dopo la prima selezione le foto passano alla fase di processamento dove è possibile configurare il processor manager in due modalità: default e underwater, a seconda della modalità scelta la pipeline di filtri che vengono applicati cambia.

Per gestire lo stato delle immagini ed il loro path è stato implmentato un promoter che ha il copito di spostare le foto, aggiornare lo stato ed il path. Tutto questo per separare la fase di processamento da quella di gestione delle cartelle durante la pipeline. 
Alla fine della fase di processing le foto hanno stato processed e si trovano nella relativa cartella pronte ad essere usate.

```
( Video ) -- > | Raw | -- > | Ingestion | -- > | Extraction | -- > | Processor | -- > | Processed |
```

### COLMAP 

COLMAP è un motore di calcolo scritto in C ottimo per la generazione di nuvole di punti sparse ricevendo in input delle immagini.

Quando viene avviata la pipeline di colmap inizia la generazione della nuvola sparsa che viene depositata in `data/colmap/sparse`: può capitare che l'algoritmo non riesca a trovare un' unica nuvola di punti unita, in tal caso verrebbe lanciato un alert e verrebbe utilizzata la nuvola più grande che è stata riconosciuta. Successivamente per orientare i dati ottenuti, a seconda della modalità di scan scelta, viene attivato l'aligner che si occupa di raddrizzare la nuvola nel piano e deposita il risultato nella cartella `data/colmap/aligned`.

E' importante non utilizzare i dati GPS in una scansione indoor perchè le camere tra loro saranno troppo vicine e l'allinemanto andrà in crash. Una volta che la nuvola sparsa è pronta i dati ottenuti vengono preparati per la fase successiva, alle immagini viene rimossa la distorsione e vine depositato tutto nella cartella `data/colmap/undistorted`.

Nella fase di matching per confrontare i punti trovati ci sono tre comandi possibili: exhaustive_matcher, sequential_matcher e spatial_metcher. Il primo confronta tutti i punti tra di loro, richiede diverso tempo se i punti sono tanti portanto la complessita a O(N^2) ed è perfetta se i punti sono pochi. Il secondo metodo consiste nel definire un numero di punti precedenti e successivi da confrontare per ogni punto, questo permette di abbassare la complessita se i punti sono molti (Es. >300). Il terzo metodo utilizza i dati gps e confronta le foto vicine tra di loro nello spazio evitando scansioni inutili, è utile quando si mappa una zaona molto larga.

COLMAP riuscirebbe a proseguire e a generare anche la nuvola di punti densa ma le prestazioni dell' algoritmo che usa sono nettamnte inferiori a quelle di OpenMVS.

Faccio menzione del file metadata_uploade.py che serviva nelle versioni precedente di colmap per preparare un database lightsql con i dati delle camere, con la versione 4.0.0 o superiore non è più necessario ed è diventato sconsigliato per non imbattersi in problemi di allinemanto dovuti al formato dei dati sul database.

```
( metadata uploading ) -- > | sparse | -- > | aligned | -- > | undisotrted |
```

### OpenMVS

OpenMVS è il motore di calcolo che utilizzo per la generazione della nuvola di punti densa a partire dai dati presenti nella cartella data/colmap/undistorted di COLMAP, infatti dispone di un interfaccia per recuperare autonomamente i dati e per generare il file .mvs che contiene tutti i dati che gli servono per partire.

Il comando per cominciare la generazione della nuvola densa è il più corposo del progetto e richiede diverso tempo di esecuzione per terminare.

OpenMVS potrebbe proseguire e generare anche la mesh texturizzata ma ho riscontrato diversi problemi nell'utilizzare i comandi, in particolare nella gen del file .mvs che contirne la mesh e le camere.

### Open3D

Open3D è lo strumento che uso per ripulire il modello, raddrizzarlo, scalarlo, texturizzarlo e visualizzarlo.

## Shooting & Asset Acquisition

## System Requirements & Performance

