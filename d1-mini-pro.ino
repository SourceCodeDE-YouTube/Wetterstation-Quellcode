@ -0,0 +1,67 @@
#include <ESP8266WiFi.h>
#include <ESP8266HTTPClient.h>
#include <WiFiClientSecureBearSSL.h>
#include <Adafruit_Sensor.h>
#include <Adafruit_BME280.h>

#define WIFI_SSID "Geheimes-Wlan"
#define WIFI_PASSWORD "EinGeheimesPasswort"
#define SERVER_URL "Geheim.net/api/receive"
#define API_PASSWORD "Geheim"  // Das API-Passwort

Adafruit_BME280 bme;
std::unique_ptr<BearSSL::WiFiClientSecure> client(new BearSSL::WiFiClientSecure);

void setup() {
    Serial.begin(115200);
    WiFi.begin(WIFI_SSID, WIFI_PASSWORD);
    Serial.print("Verbinde mit WLAN...");
    
    while (WiFi.status() != WL_CONNECTED) {
        delay(1000);
        Serial.print(".");
    }
    Serial.println("\nVerbunden mit WLAN!");
    
    if (!bme.begin(0x76)) {
        Serial.println("BME280 nicht gefunden!");
        while (1);
    }

    // HTTPS-Zertifikatsprüfung deaktivieren
    client->setInsecure();
}

void loop() {
    if (WiFi.status() == WL_CONNECTED) {
        HTTPClient http;
        http.begin(*client, SERVER_URL);
        http.addHeader("Content-Type", "application/json");
        http.addHeader("Origin", "https://geheim.net");  // CORS-Unterstützung

        float temperatur = bme.readTemperature();
        float luftfeuchtigkeit = bme.readHumidity();
        float luftdruck = bme.readPressure() / 100.0F;

        String jsonPayload = "{";
        jsonPayload += "\"password\":\"" + String(API_PASSWORD) + "\",";
        jsonPayload += "\"temperatur\":" + String(temperatur) + ",";
        jsonPayload += "\"luftfeuchtigkeit\":" + String(luftfeuchtigkeit) + ",";
        jsonPayload += "\"luftdruck\":" + String(luftdruck);
        jsonPayload += "}";

        http.setTimeout(5000);  // Timeout auf 5 Sekunden setzen
        int httpResponseCode = http.POST(jsonPayload);

        Serial.print("Server Antwort: ");
        Serial.println(httpResponseCode);

        http.end();
    } else {
        Serial.println("WLAN getrennt! Versuche erneut...");
        WiFi.disconnect();
        WiFi.begin(WIFI_SSID, WIFI_PASSWORD);
    }

    delay(60000); // 1 Minute warten
}
