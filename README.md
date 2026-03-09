# Digital Twin

## appunti veloci

link per dual twin esempio risultato : https://application.utwin.it/devForgeViewer?developerId=090eef94-8a39-49a9-a47e-79a7ada8b517&projectId=86530938-6679-42e8-9012-37c9d75b5f24&modelPath=%2FTimelapse%20Lab%2FTelecamere%20cantiere%20Timelapse%20Lab.rvt

link progetto : https://github.com/EdoPoltro/progetto-digital-twin.git

flusso : 
- inanzi tutto la parte fondamentale e capire quante immagini prendere e come devono essere angolate per ottenre la massima resa
    poi tramite degli algoritmi dovro filtrare queste immagini e renderele piu pulite possibili, in caso di di scatti sotto acqua sarà utile implementare un algoritmo che rimuova le particelle associate all'acqua.
- la seconda fase cosniste nella modellazione 3d degli oggetti, tramite una libreria posso puntizzare il mio oggetto per segnalarne poi spigoli, lati, ecc. da questo primo modello poi posso realizzare il mio file 3d in formato : .obj .fbx .gltf .glb (da scegliere il migliore che lo usero per l'output del programma). per la stampa 3d il formato è .stl, mentre per autocad è .step .3mf

OpenCV : libreria python per la correzione dei colori
Open3D o PyVista : nuvole di punti
AliceVision / Meshroom (via API) : ricostruzione 3D
Flask o Fast API : interfaccia web
watchdog : modifica in tempo reale delle foto

pip freeze > requirements.txt per salvare le librerie su requirements.txt

## struttura del progetto

progetto-digital-twin :

## obiettivi

capire come scattare le foto per una massima resa 

## parametri da salvare 

A. Parametri della Camera (Intrinseci):

Focal Length: Fondamentale per il software 3D.

Sensor Size: Per calcolare il rapporto pixel/metri.

B. Parametri di Posizionamento (Georeferenziazione):

Coordinate (X, Y, Z): Se hai un GPS (o un sistema di posizionamento acustico sott'acqua).

Orientamento (Pitch, Roll, Yaw): Per sapere come era inclinata la camera.

C. Parametri Ambientali (Il vero "Twin"):

GSD (Ground Sample Distance): Quanti centimetri reali rappresenta un pixel (es. 1 pixel = 0.5 cm).

Timestamp: Data e ora precisa (per analisi temporali).

Torbidità/Luce: (Se hai sensori) per giustificare eventuali errori nel modello.

## avvio progetto 

1. creare la venv : py -3.11 -m venv venv

2. attivare la venv : .\venv\Scripts\activate

3. aggiornare il file requirements.txt

4. scaricare le libreire : pip install -r requirements.txt (prima aggiornare pip) 
ricordo che open3d e molto esigente sulla versione di python e accetta solo fino al 3.11

## costruzione del modello dell'immagine 

usando il decoratore @dataclass si costruisce l'istanza con i parametri, usa i valori default se inizializzati,
ho creato un enum per lo stato una classe generale per le caputred Images e due classi specifiche per i metadati della camera e spaziali.

## file config.py
in quetso file centralizzo luso dei path e dei dati per avere solo una ricorrenza nel caso andassero cambiati 

## gestione delle eccezioni per il debug

chiamo la baseError come exception di default poi in base al tipo mi da il suggest e importante che quando 
faccio il raise poi quando chiamo la funzione faccio il blocco try except

## metadata extractor
usndo pillow devo scorporare i file immagini per estrarre i dati EXIF 
implemento una funzione void che mi update le istanze di CapturedImage che gestisce la seconda fase della pipeline 

creo due nuove eccezioniper gestire i casi del load dei metadata

width serve per chiudere i file immagine se scoppia un eccezione o se termina l'estrazione 

uso i dati exif incapsulati nelle foto li traduco con la libreria tags in un dict ma prima lo estendo con un sotto dizionario presente in exif data per prendere anche il valore della focale. eseguo questo per tutte le foto

(mancano i dati gps e i dati di localizzazione)

