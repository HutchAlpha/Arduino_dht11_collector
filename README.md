
Dans l'invite de commandes, tape :


python -m pip install pyserial matplotlib

Si tu as un message d'erreur avec pip, essaye :

python -m ensurepip --upgrade
python -m pip install --upgrade pip
python -m pip install pyserial matplotlib

3. Installer la bibliothèque DHT pour Arduino

3.1. Via le gestionnaire de bibliothèques
Ouvre Arduino IDE.

Menu Croquis → Inclure une bibliothèque → Gérer les bibliothèques...

Dans la barre de recherche, tape dht.

Installe :

DHT sensor library by Adafruit (version 1.4.x),

6.1. Depuis l'invite de commandes dans cmd :


python "C:\Users\oui\Desktop\Projet Arduino\TemperatureHumid\arduino_dht11_collector.py"

6.2. Depuis le dossier du projet
text
cd "C:\Users\oui\Desktop\Projet Arduino\TemperatureHumid"
python arduino_dht11_collector_v2.py
7. Utilisation de l'application
Branche ton Arduino Uno via USB.

Lance l'application Python.

Dans la liste Port Serie, choisis COMx (Windows) correspondant a ta carte.

Clique sur Demarrer la collecte.

Tu vois :

les lignes du moniteur serie Arduino,

les valeurs de temperature / humidite en temps reel,

le nombre de mesures.

Tu peux ensuite :

Afficher les statistiques,

Generer les graphiques,

Exporter en CSV.

8. Graphiques et statistiques
L'app Python genere :

un graphique Temperature vs Temps (ligne rouge) avec moyenne et ecart-type,

un graphique Humidite vs Temps (ligne bleue) avec moyenne et ecart-type,

un fichier dht11_chart_YYYYMMDD_HHMMSS.png.

Tu peux ouvrir l'image pour voir l'evolution de la piece ou la zone mesuree.

9. Resume ultra simple
Installer Python via Microsoft Store.

Installer pyserial et matplotlib :

text
python -m pip install pyserial matplotlib
Installer DHT sensor library et Adafruit Unified Sensor dans Arduino IDE.

Flasher le code Arduino.

Lancer :


python "C:\Users\oui\Desktop\Projet Arduino\TemperatureHumid\arduino_dht11_collector.py"
Choisir le port serie, cliquer Demarrer.


Tu as maintenant une mini station meteo avec stats et graphes !
