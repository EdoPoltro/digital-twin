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
OpenMVG ricostruzione 3D
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

i dati gps sono salvati in tuple di tuple ((x, y),(x, y),(x, y)) si ottengono sempre dai dati exif (sto valutando di separare in due funzioni per i dati della camera dai dati del gps per avere una maggiore separazione). inoltre sto valutando che qualora ci sia un problema di una sola immagine non devo lanciare un eccezione che va a main ma devo scartare la foto e gestire leccezione nella funzione con il for

si possono adottare due approcci per la gestione degli errori: o scarto la foto subito, o se magari una foto ha risoluzione ottima ma mancano i dati gps li metto a none e tengo la foto -> per semplicita di implementazione per ora tengo la prima opzione 
va discusso il quando scartare una foto per quali dati mancanti pero ra do peso piu al gps 

## cartella data 
ho reso piu rigorosa la struttura della cartella data per sapere in ogni fase della pipeline dove viaggiano i miei dati con input raw , interim (le foto passate dai filtri ma ancora di brutta copia, se non mi soddisfano posso scartarle e passare altri filtri e ricominciare da raw), processed (il dataset finale), output (i modelli generati ).

per ottenere la dimensione del sensore devo scaricare un database in json e caricarlo in SENSOR_DB_DIR

ho scartato lestrazione del senso dimension dal json perche non aveva tutte le dimensioni che mi servivano quindi ho iniziato a calolare la dimensione tramite una formula cosi sono sicuro che se ci sono i due campi del local len allora la calola sempre ( non ho gestito le exception ancora per un paio di occasioni perche devo capire meglio e piu rigorosamente quando scartare un immagine se mancano i dati) 

ho fatto su helper per aprire i file json e restituire un dict anche se non servira pero lho fatta 

ho scartato anche orientation perche allinzio la intendevo in modo diverso come se fosse un drone che scattava le foto. e tramite gli exif era possibile solo estrarre se la foto era fatta im verticale o orizzontale.

## 11/03/2026 :

implemento la soft delete per le immagini e modifico metadata_extractor.py e studio piu rigorosamente la gli errori nelle immagini:
un immagina va in error se:
- non si apre o e corratta
- no focal length
- no foacl length 35mm
- no resolution
- no lon o len 

creato la funzione per la promozione delle foto e le sottofunzioni e quella per ripulre lambiente 

ok a questo punto costruisci con colmap la nuvola di punti e il modello 3d e con open3d pulisco il risultato e lo visualizzo 

12/03/2026 

oggi ho proseguito allimplementazione del colmap manager e ho capito che e una tecnologia che e specifica

ora funziona processa servono almeno 15 immagini e non devo cercare di mappare un oggetto trasparente, inoltre ho diminuito il numero max di threads perche andava in crash il programma e ho staccato luso della mia scheda video perche non e nvidia.

come scattare: 20 - 30 foto muovendosi a cerchio su diversi piani di altezza e angolazione fissando loggetto, luce naturale e morbida e un fondo di giornale con tanti punti o cartina geografica insimma cose con molti dettagli 

13/03/2026 
creo il servizio per iniziare a riorganizzare col map, sposto in altri due file la generazionedel db e la generazione del file txt
l'overlap se messo a 10 quando col map confronta la foto 50 su 100 la confronta con le altre foto tra 40 e 60 

16/03/2026

ho scoeprto che non sempre servono i dati gps perche vengono usati nella fase appena successiva della creazione della nuvola sparsa ma solo in caso di ambienti outdoor se le foto sono in uno spazio troppo ristretto il calcolo fallirà.
va leggermetne modificato il criterio di scarto delle foto

17/03/2026 

terminata la ristrutturazione generale dell'app, rimane da decidere la soft delite o la cancellazione diretta con filter (in ogni caso prima di colmap devo avere un array pulito), da sistemare le exception, da implmentare le funzionalita legate al flag SCAN_MODE, e continuare con aligned e la nuvola di punti densa