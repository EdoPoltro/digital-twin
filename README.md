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

ho scoperto che per la costruzione della nuvola densa non si puo non usare la scheda video nvidia quindi sto valutando un alternativa (openmvs), open3d invece lo usiamo per la fase successiva (mesh) perche e ottimo per modellare il 3d ma non e in grado di crearlo a partire dalle immagini.
openmvs e famoso per prendere i dati da colmap (nuvola sparsa) e creare la rispettiva nuvola densa .ply

1. COLMAP (Il Geometra)
Cosa fa: Estrae i punti chiave, capisce la posizione delle fotocamere nello spazio, crea la Nuvola Sparsa e (se sei outdoor) fa l'Allineamento GPS.

Perché lui: È il re indiscusso dello Structure from Motion (SfM). Nessuno calcola lo spazio meglio di lui. Alla fine, esporta un file pacchetto per OpenMVS.

2. OpenMVS (Il Costruttore)
Cosa fa: Prende i dati di COLMAP e genera la Nuvola Densa.

✨ Il colpo di scena sulla Mesh: Ti consiglio di far fare la Mesh e la Texture a OpenMVS, non a Open3D! OpenMVS ha dei moduli specifici (ReconstructMesh e TextureMesh) che non solo creano la pelle solida, ma proiettano le tue fotografie originali sopra la Mesh, rendendola identica alla realtà (il vero Digital Twin). Open3D fa molta fatica a "colorare" bene una mesh partendo dalle foto.

3. Open3D (L'Ispettore / L'Ingegnere)
Cosa fa: Prende la Mesh texturizzata (o la Nuvola Densa) finale generata da OpenMVS, la apre a schermo e ti permette di fare le operazioni ingegneristiche:

Scalatura (Indoor): Clicchi su due punti dello scatolone, gli dici "sono 45 cm" e lui ridimensiona tutto il modello 3D nel mondo reale.

Pulizia: Tagli via il pavimento o i pezzi di stanza che non ti interessano (Cropping).

Misurazioni: Calcoli volumi, distanze o aree.

ok questa parte e presa da gemini comuqnue voglio rimuovere la parte di mesh e dense da colmap perche non posso fare il dense senza una scheda video nvidia ma comunque sarebbe meno efficiente rispetto ad usare openmvs quidni riorganizzo il progetto e le cartelle data e creo tre manage per le tre parti

19/03/2026

ho ottenuto la prima nuvola di punti densa: ho modificato il colmap manager ora come ultimo passaggio converto le foto in undistorted e succesivamente importo il model.mvs, successivamente quando sono pronto lancio il comando per generare la nuvola di punti

ho implmentato il poisson matcher ma fa abbassare veramente tanto la qualita del mesh quindi sto cercando un alternativa.

23/03/2026 
negli ultimi due giorni ho lavorato 2 ore (weekend) e ho fatto tetst+ refactorign codice, ho visto che se attivo la modalita gpu sulla creazione della nuvola sparsa va di brutto. il risultato e pressoche uguale ma in termini di tempo ci mette pochissimo.

ora scarico open3d : import open3d as o3d ( libreria python)
pip install open3d

24 / 03 /2026 
il problema di reconstructorMesh penso che fosse dovuto alla versione 2.4 quindi lho sostituita con la 2.2 ma non posso testarla su questo pc per problemi di ram pero il codice di errore e cambiato. 
ho proseguito con il processor manager, ho creato un wrapper per non dover clonare ogni volta il codice e ho aggiunto la pipeline underwater che impiega deisamente piu tempo di calcolo della standard quindi introduco un caricamento 

dopo non pochi problemi ho abortito la barra di caricamento e reconstruct mesh non funziona almeno con il processore percio faccio un tentativo con open3d.

ok ho provato ad usare open3d non e male, non so come sarebbe dovuto venire con openmvs ma quello generato da open3d e molto carino, ovviamente dopo lo texturizzo rimuovo il rumore, ora definisco allora il ciclo: genero con colmap la nuvola sparsa, aligned e le immagini undistorted, poi con open mvs la nuvola densa e poi ricostruisco la mesh con open 3d la texturizzo e tolgo il rumore. 