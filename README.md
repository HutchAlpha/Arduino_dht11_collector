# Station météo DHT11 avec Arduino Uno

Application Python de collecte et de visualisation en temps réel de la température et de l'humidité mesurées avec un capteur DHT11 relié à un Arduino Uno.

## Fonctionnalités

- Lecture automatique des données envoyées par l'Arduino via le port série
- Affichage en temps réel de la température, de l'humidité et du nombre de mesures
- Courbe de température, courbe d'humidité et moyenne progressive
- Détection visuelle des records minimum et maximum
- Bruitage optionnel lors d'un nouveau record strict
- Légende et points de records masquables
- Export des mesures en CSV

---

## 1. Prérequis

- Windows 10 ou Windows 11
- Arduino Uno et câble USB de données
- Capteur DHT11
- Arduino IDE
- Python 3

> Si la commande `python` n'est pas reconnue, installe Python depuis le Microsoft Store ou depuis le site officiel de Python. Ferme puis rouvre l'invite de commandes après l'installation.

---

## 2. Installer les dépendances Python

Ouvre l'**Invite de commandes** (`cmd`) puis lance :

```cmd
python -m pip install pyserial matplotlib
```

### Si `pip` génère une erreur

Exécute les commandes suivantes une par une :

```cmd
python -m ensurepip --upgrade
python -m pip install --upgrade pip
python -m pip install pyserial matplotlib
```

Ces paquets sont nécessaires pour :

- `pyserial` : communiquer avec l'Arduino via USB / port série
- `matplotlib` : afficher les graphiques en direct

---

## 3. Installer la bibliothèque DHT

### 3.1 Via le gestionnaire de bibliothèques Arduino

1. Ouvre **Arduino IDE**.
2. Clique sur **Croquis → Inclure une bibliothèque → Gérer les bibliothèques...**
3. Dans la barre de recherche, tape :

   ```text
   dht
   ```

4. Installe la bibliothèque :

   ```text
   DHT sensor library by Adafruit
   ```

   Version recommandée : `1.4.x`.

5. Installe également la dépendance suivante si Arduino IDE la demande ou si elle n'est pas déjà présente :

   ```text
   Adafruit Unified Sensor
   ```

---

## 4. Câblage du DHT11

Pour un module DHT11 à trois broches :

| DHT11 | Arduino Uno |
|---|---|
| `+` / `VCC` | `5V` |
| `-` / `GND` | `GND` |
| `S` / `DATA` | `D2` |

Le code Arduino utilise donc la broche numérique `2` :

```cpp
#define DHTPIN 2
#define DHTTYPE DHT11
```

> Si ton DHT11 est un capteur nu à quatre broches, ajoute une résistance de pull-up entre `VCC` et `DATA` (en général entre 4,7 kΩ et 10 kΩ).

---

## 5. Code Arduino

Téléverse ce sketch sur l'Arduino Uno. Il envoie une mesure toutes les deux secondes au format attendu par l'application Python : `DATA:temperature,humidite`.

```cpp
#include <DHT.h>

#define DHTPIN 2
#define DHTTYPE DHT11

DHT dht(DHTPIN, DHTTYPE);

void setup() {
  Serial.begin(9600);
  dht.begin();

  Serial.println("Station DHT11 demarree");
}

void loop() {
  delay(2000);

  float temperature = dht.readTemperature();
  float humidite = dht.readHumidity();

  if (isnan(temperature) || isnan(humidite)) {
    Serial.println("Erreur lecture capteur DHT11");
    return;
  }

  Serial.print("Temperature = ");
  Serial.print(temperature);
  Serial.print(" C | Humidite = ");
  Serial.print(humidite);
  Serial.println(" %");

  Serial.print("DATA:");
  Serial.print(temperature);
  Serial.print(",");
  Serial.println(humidite);
}
```

### Vérification

1. Dans Arduino IDE, sélectionne **Outils → Type de carte → Arduino Uno**.
2. Sélectionne le bon port dans **Outils → Port** (par exemple `COM3`).
3. Téléverse le sketch.
4. Ouvre le **Moniteur série** et règle la vitesse sur **9600 bauds**.

Tu dois voir des lignes semblables à :

```text
Temperature = 24.0 C | Humidite = 58.0 %
DATA:24.0,58.0
```

> Ferme le Moniteur série avant de lancer le programme Python : un seul logiciel peut utiliser le port `COM` à la fois.

---

## 6. Lancer l'application Python

Le fichier de l'application s'appelle toujours :

```text
arduino_dht11_collector.py
```

### 6.1 Depuis n'importe quel dossier

Dans `cmd`, lance :

```cmd
python "C:\Users\oui\Desktop\Projet Arduino\TemperatureHumid\arduino_dht11_collector.py"
```

### 6.2 Depuis le dossier du projet

```cmd
cd "C:\Users\oui\Desktop\Projet Arduino\TemperatureHumid"
python arduino_dht11_collector.py
```

L'application cherche automatiquement le premier port série disponible et démarre la collecte.

---

## 7. Utiliser l'application

1. Branche l'Arduino Uno via USB.
2. Vérifie que le Moniteur série Arduino est fermé.
3. Lance l'application Python.
4. L'application se connecte automatiquement au port série disponible.

Tu vois alors :

- La température et l'humidité en temps réel
- Le nombre de mesures reçues
- La moyenne progressive de température
- Le minimum, le maximum et la moyenne d'humidité
- Les courbes en direct
- Le journal des messages reçus depuis l'Arduino

### Boutons disponibles

| Bouton | Action |
|---|---|
| `Rafraîchir` | Recherche les ports série disponibles |
| `Exporter CSV` | Enregistre les mesures dans `mesures_dht11.csv` |
| `Bruitage : activé / désactivé` | Active ou coupe les alertes sonores de records |
| `Afficher / Masquer légende` | Affiche ou masque la légende de température |
| `Masquer / Afficher points records` | Affiche ou masque les points de records sur le graphique |

### Records de température

- Un nouveau maximum déclenche un bip aigu
- Un nouveau minimum déclenche un bip grave
- Une valeur qui égale un record ne déclenche pas de bruit
- Les anciens records apparaissent avec des points plus clairs

---

## 8. Graphiques et export

L'application affiche en direct :

- **Température vs temps** : ligne rouge
- **Moyenne progressive** : ligne violette en pointillés
- **Humidité vs temps** : ligne bleue
- **Records min/max** : points de couleur, désactivables via un bouton

L'export crée le fichier :

```text
mesures_dht11.csv
```

Le CSV contient :

- Date et heure
- Température
- Humidité
- Moyenne progressive de température
- Événement éventuel (`new_max`, `new_min`, `equal_max`, `equal_min`)

Le fichier est encodé en `UTF-8-SIG` et séparé par `;`, ce qui facilite son ouverture dans Excel sous Windows.

---

## 9. Dépannage

### `python` ou `pip` n'est pas reconnu

Installe Python, ferme l'invite de commandes et ouvre-en une nouvelle. Vérifie ensuite :

```cmd
python --version
```

### `Access denied` / `Accès refusé` sur COM3

Le port est déjà ouvert par un autre programme. Ferme :

- Le Moniteur série Arduino
- Le Traceur série Arduino
- L'application Python déjà ouverte
- Tout logiciel utilisant le même port COM

Puis relance l'upload Arduino ou l'application Python.

### `DHT.h: No such file or directory`

Installe **DHT sensor library by Adafruit** et **Adafruit Unified Sensor** depuis le gestionnaire de bibliothèques Arduino.

### L'application ne reçoit aucune donnée

Vérifie que l'Arduino envoie bien une ligne :

```text
DATA:24.0,58.0
```

Vérifie également que la vitesse série est `9600` dans l'Arduino et dans l'application.

---

## Résumé rapide

1. Installe Python.
2. Installe les paquets Python :

   ```cmd
   python -m pip install pyserial matplotlib
   ```

3. Installe `DHT sensor library by Adafruit` et `Adafruit Unified Sensor` dans Arduino IDE.
4. Téléverse le sketch Arduino.
5. Ferme le Moniteur série.
6. Lance l'application :

   ```cmd
   python "C:\Users\oui\Desktop\Projet Arduino\TemperatureHumid\arduino_dht11_collector.py"
   ```

Tu disposes maintenant d'une mini station météo avec collecte série, statistiques, graphiques temps réel, records et export CSV.
