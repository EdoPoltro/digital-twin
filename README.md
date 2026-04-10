# Digital twin

## Descrizione

L'applicazione è in grado di elaborare una serie di immagini, processarle e tramite COLMAP, OpenMVS e Open3D di generare una nuvola sparsa, una nuvola densa e una mesh texturizzata.

L'applicazione inoltre riesce a gestire due modailta di scan (indoor e outdoor) per la mappatura di aree molto piccole, come ambienti domestici e aree relativamente grandi come case o strutture. a seconda della modalita di scan viene avviata una pipeline dedicata.

## Environment setup per windows

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

## Environment setup per linux

Per preparare l'ambiente in lunx va cambiata leggermente la logica:

- Al posto di scaricare la cartella di COLMAP con gli eseguibili va installato tramite conda un ambiente di esecuzione dedicato con i comandi `conda create -n colmap -c conda-forge colmap=4.0.2 -y` e `conda activate colmap`, se ci sono problemi di esecuzione va controllata la vesione di CUDA. Per OpenMVS va scaricata semplicemente la distriubuzione degli eseguibili dedicata al sistema linux.

- Vanno assegnati i diritti di esecuzione ai file di OpenMVS: `chmod +x ./engines/openmvs/*`.

- Attenzione scaricare python solo dopo COLMAP. Per scaricare python e creare la venv vanno lanciati i seguenti comandi in ordine: `sudo apt update`, `sudo apt install software-properties-common -y`, `sudo add-apt-repository ppa:deadsnakes/ppa -y`, `sudo apt update`, `sudo apt install python3.11 python3.11-venv python3.11-dev -y`, poi all'interno della cartella del progetto `python3.11 -m venv venv` e `source venv/bin/activate`.

- Per scaricare file da google drvie (foto / video) eseguo `pip install gdown` e `gdown --id < link > -O < output_file_path >`.

## Struttura del progetto

```
progetto_digital_twin
|_ data
|   |_ processing
|   |   |_ video
|   |   |_ raw  < ---- input image
|   |   |_ processed
|   |_ colmap
|   |_ openmvs
|   |_ open3d  < ---- result model
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

Se il programma è in modalità indoor allora effettuerà con open3d la fase di scaling, se il programma è in outdoor mode il programma effettuerà le fasi di GPS metadata uploading.

```
| Ingestion | -- > | Processing | -- > ( Metadata uploading ) --
                                                                 |
                                                                 |
 ------- | Undistorting | < -- | Aligning | < -- | Sparse | < --
|
|
 -- > | Dense | --> | Mesh | -- > | Refine | -- > | Texture | --
                                                                 |
                                                                 |
 --- ( Scaling ) < -- | Smoothing | < -- | Noise removing | < --
|
|
 -- > | Exportation | 
 ```

Una volta caricate le immagini scattate nella cartella `progetto_digital_twin/data/processing/raw` o caricato un video nella cartella `progetto_digital_twin/data/processing/raw` il programma seguirà la pipeline associata alla modalita di scan e otterrà il modello in formato obj.

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
( Metadata uploading ) -- > | Sparse | -- > | Aligned | -- > | Undisotrted |
```

### OpenMVS

Con OpenMVS riesco a generare la nuvola di punti densa a partire dai dati forniti da COLMAP e successivamente la mesh, la mesh raffinata e la mesh texturizzata.
Per usare correttamnte OpenMVS è necessario impostare la cartella di lavoro quando si lancia il subprocess per evitare problemi di path.

Nelle versione 2.4 di OpenMVS c'è un bug nella texturizzazione della mesh e per procedere con la pipeline e necessario disabilitare i flag `--local-seam-leveling` e `--global-seam-leveling`.
In maniera alternativa è possibile passare alla versione 2.1 facendo pero attenzione ai nomi dei flag.

```
| Importation | -- > | Dense | -- > | Mesh | -- > | Refine | -- > | Texture |
```

### Open3D

Open3D viene usato per ripulire, scalare e riallineare il modello finale. 

```
| Importation | -- > | Topological cleaning | -- > | Noise removal | -- > | Alignement | -- > 

( Scaling ) -- > | Smoothing | -- > | Exportation |
```

## Shooting & Asset Acquisition

E' consigliata la modalità video per inizializzare i dati nel programma perchè è in grado di generare molte piu foto significative per l'elaborazione.

Durante la fase di ripresa e consigliato eseguire prima uno scan generare dell'area girandoci attorno da varie altezze e poi di avvicinarsi agli spigoli ed ai dettagli per aggiungere informazione ai frame. Più lungo sarà il video e più frame si potranno ricavare e maggiore saranno le prestazioni del modello finale, ovviamente la quantità di foto e direttamente proporzionale al tempo di esecuzione.

## System Requirements & Performance

Il progetto per eleaborare in modo efficente senza crash necessita di una buona RAM (minimo 8GB) e di una scheda video NVIDIA: è possibile disabilitare il flag use_gpu ma questo comporterebbe un aumento del tempo di calcolo.

Il progetto deve elaborare una grande quantità di frame quindi utilizzare un pc con poca RAM potrebbe causare l'itnterruzione dell'esecuzione del programma.

