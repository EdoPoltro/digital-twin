# Digital Twin

## appunti veloci

link per dual twin esempio risultato : https://application.utwin.it/devForgeViewer?developerId=090eef94-8a39-49a9-a47e-79a7ada8b517&projectId=86530938-6679-42e8-9012-37c9d75b5f24&modelPath=%2FTimelapse%20Lab%2FTelecamere%20cantiere%20Timelapse%20Lab.rvt

flusso : 
- inanzi tutto la parte fondamentale e capire quante immagini prendere e come devono essere angolate per ottenre la massima resa
    poi tramite degli algoritmi dovro filtrare queste immagini e renderele piu pulite possibili, in caso di di scatti sotto acqua sarà utile implementare un algoritmo che rimuova le particelle associate all'acqua.
- la seconda fase cosniste nella modellazione 3d degli oggetti, tramite una libreria posso puntizzare il mio oggetto per segnalarne poi spigoli, lati, ecc. da questo primo modello poi posso realizzare il mio file 3d in formato : .obj .fbx .gltf .glb (da scegliere il migliore che lo usero per l'output del programma). per la stampa 3d il formato è .stl, mentre per autocad è .step .3mf

OpenCV : libreria python per la correzione dei colori
Open3D o PyVista : nuvole di punti
AliceVision / Meshroom (via API) : ricostruzione 3D
Flask o Fast API : interfaccia web
watchdog : modifica in tempo reale delle foto

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