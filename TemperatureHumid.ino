#include <DHT.h>
#include <Wire.h>
#include <LiquidCrystal_I2C.h>

#define DHTPIN 2      // Pin de données
#define DHTTYPE DHT11 // Type de capteur

DHT dht(DHTPIN, DHTTYPE);

// Adresse I2C la plus courante : 0x27 (parfois 0x3F selon le module)
// Format : LiquidCrystal_I2C(adresse, colonnes, lignes)
LiquidCrystal_I2C lcd(0x27, 16, 2);

void setup() {
  Serial.begin(9600);
  dht.begin();

  lcd.init();       // initialise le LCD
  lcd.backlight();  // allume le rétroéclairage

  lcd.setCursor(0, 0);
  lcd.print("Station DHT11");
  lcd.setCursor(0, 1);
  lcd.print("Demarrage...");

  Serial.println("=== Station DHT11 ===");
  Serial.println("Demarrage...");

  delay(1500);
  lcd.clear();
}

void loop() {
  delay(2000); // 2 secondes entre chaque mesure

  float temperature = dht.readTemperature();
  float humidite   = dht.readHumidity();

  if (isnan(temperature) || isnan(humidite)) {
    Serial.println("Erreur lecture capteur DHT11 (nan)");

    lcd.setCursor(0, 0);
    lcd.print("Erreur capteur ");
    lcd.setCursor(0, 1);
    lcd.print("DHT11 (nan)     ");
    return; // ne rien envoyer si la lecture est invalide
  }

  // Affichage lisible sur le Serial
  Serial.print("Temperature = ");
  Serial.print(temperature);
  Serial.print(" °C | Humidite = ");
  Serial.print(humidite);
  Serial.println(" %");

  // Ligne pour Python (si tu l'utilises)
  Serial.print("DATA:");
  Serial.print(temperature);
  Serial.print(",");
  Serial.println(humidite);

  // Affichage sur l'écran LCD
  lcd.setCursor(0, 0);
  lcd.print("Temp: ");
  lcd.print(temperature, 1);
  lcd.print((char)223); // symbole degré °
  lcd.print("C   ");

  lcd.setCursor(0, 1);
  lcd.print("Hum:  ");
  lcd.print(humidite, 1);
  lcd.print(" %   ");
}