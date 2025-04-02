from flask import Flask, request, jsonify
from flask_cors import CORS
import json
import threading
import time
from datetime import datetime, timedelta

app = Flask(__name__)
CORS(app)

WETTER_DATEI = "wetter.json"
DAILY_DATEI = "daily.json"
WEEKLY_DATEI = "weekly.json"
PASSWORT = "das-api-password-was-der-d1-mini-pro-mitsendet"

@app.route("/api/latest", methods=["GET"])
def get_latest():
    daten = lade_daten(WETTER_DATEI)
    if daten:
        return jsonify(daten[-1])
    return jsonify({"error": "Keine Daten vorhanden"}), 404

@app.route("/api/daily", methods=["GET"])
def get_daily():
    daten = lade_daten(DAILY_DATEI)
    return jsonify(daten)

@app.route("/api/weekly", methods=["GET"])
def get_weekly():
    daten = lade_daten(WEEKLY_DATEI)
    return jsonify(daten)

def lade_daten(datei):
    try:
        with open(datei, "r") as file:
            return json.load(file)
    except (FileNotFoundError, json.JSONDecodeError):
        return []

def speichere_daten(datei, daten):
    with open(datei, "w") as file:
        json.dump(daten, file, indent=4)

@app.route("/api/receive", methods=["POST"])
def receive_data():
    data = request.json
    if not data or data.get("password") != PASSWORT:
        return jsonify({"error": "Ungueltiges Passwort"}), 403

    temperatur = data.get("temperatur")
    luftfeuchtigkeit = data.get("luftfeuchtigkeit")
    luftdruck = data.get("luftdruck")
    
    if temperatur is None or luftfeuchtigkeit is None or luftdruck is None:
        return jsonify({"error": "Fehlende Daten"}), 400

    neue_daten = lade_daten(WETTER_DATEI)
    neue_daten.append({
        "temperatur": temperatur,
        "luftfeuchtigkeit": luftfeuchtigkeit,
        "luftdruck": luftdruck,
        "zeit": datetime.now().strftime("%Y-%m-%d %H:%M:%S")
    })
    
    speichere_daten(WETTER_DATEI, neue_daten)
    return jsonify({"success": "Daten gespeichert"}), 200

@app.route("/api/diagramm", methods=["GET"])
def get_diagramm():
    daten = lade_daten(WETTER_DATEI)
    jetzt = datetime.now()
    acht_stunden_ago = jetzt - timedelta(hours=8)
    
    gefilterte_daten = [d for d in daten if datetime.strptime(d["zeit"], "%Y-%m-%d %H:%M:%S") >= acht_stunden_ago]
    
    stundenwerte = {}
    for eintrag in gefilterte_daten:
        zeitstempel = datetime.strptime(eintrag["zeit"], "%Y-%m-%d %H:%M:%S")
        stunde = zeitstempel.replace(minute=0, second=0)
        
        if stunde not in stundenwerte:
            stundenwerte[stunde] = {"temperatur": [], "luftfeuchtigkeit": [], "luftdruck": []}
        
        stundenwerte[stunde]["temperatur"].append(eintrag["temperatur"])
        stundenwerte[stunde]["luftfeuchtigkeit"].append(eintrag["luftfeuchtigkeit"])
        stundenwerte[stunde]["luftdruck"].append(eintrag["luftdruck"])
    
    durchschnittswerte = []
    for stunde, werte in sorted(stundenwerte.items()):
        durchschnittswerte.append({
            "zeit": stunde.strftime("%Y-%m-%d %H:%M:%S"),
            "temperatur": sum(werte["temperatur"]) / len(werte["temperatur"]),
            "luftfeuchtigkeit": sum(werte["luftfeuchtigkeit"]) / len(werte["luftfeuchtigkeit"]),
            "luftdruck": sum(werte["luftdruck"]) / len(werte["luftdruck"])
        })
    
    return jsonify(durchschnittswerte)

def speichere_tageswerte():
    while True:
        jetzt = datetime.now()
        if jetzt.hour == 23 and jetzt.minute == 59:  # Jeden Tag um 23:59
            daten = lade_daten(WETTER_DATEI)
            if daten:
                max_temp = max(d["temperatur"] for d in daten)
                min_temp = min(d["temperatur"] for d in daten)
                max_luftf = max(d["luftfeuchtigkeit"] for d in daten)
                min_luftf = min(d["luftfeuchtigkeit"] for d in daten)
                max_druck = max(d["luftdruck"] for d in daten)
                min_druck = min(d["luftdruck"] for d in daten)

                tageswerte = {
                    "datum": jetzt.strftime("%Y-%m-%d"),
                    "max-temp": max_temp,
                    "min-temp": min_temp,
                    "max-luftf": max_luftf,
                    "min-luftf": min_luftf,
                    "max-druck": max_druck,
                    "min-druck": min_druck
                }

                alte_werte = lade_daten(DAILY_DATEI)
                alte_werte.append(tageswerte)
                speichere_daten(DAILY_DATEI, alte_werte)

                # wetter.json leeren
                speichere_daten(WETTER_DATEI, [])
                print("Tageswerte gespeichert und wetter.json geleert")

        time.sleep(60)  # Alle 60 Sekunden prüfen

# Hintergrund-Thread für das Speichern der Tageswerte starten
threading.Thread(target=speichere_tageswerte, daemon=True).start()

def speichere_wochenwerte():
    while True:
        jetzt = datetime.now()
        if jetzt.weekday() == 6 and jetzt.hour == 23 and jetzt.minute == 59:  # Sonntag 23:59
            daten = lade_daten(DAILY_DATEI)
            if daten:
                max_temp = max(d["max-temp"] for d in daten)
                min_temp = min(d["min-temp"] for d in daten)
                max_luftf = max(d["max-luftf"] for d in daten)
                min_luftf = min(d["min-luftf"] for d in daten)
                max_druck = max(d["max-druck"] for d in daten)
                min_druck = min(d["min-druck"] for d in daten)

                wochenwerte = {
                    "datum": jetzt.strftime("%Y-%m-%d"),
                    "max-temperatur": max_temp,
                    "min-temperatur": min_temp,
                    "max-luftfeuchtigkeit": max_luftf,
                    "min-luftfeuchtigkeit": min_luftf,
                    "max-luftdruck": max_druck,
                    "min-luftdruck": min_druck
                }

                alte_werte = lade_daten(WEEKLY_DATEI)
                alte_werte.append(wochenwerte)
                speichere_daten(WEEKLY_DATEI, alte_werte)

                # daily.json leeren
                speichere_daten(DAILY_DATEI, [])
                print("Wochenwerte gespeichert und daily.json geleert")

        time.sleep(60)  # Alle 60 Sekunden prüfen

# Hintergrund-Thread für das Speichern der Wochenwerte starten
threading.Thread(target=speichere_wochenwerte, daemon=True).start()

if __name__ == "__main__":
    app.run(host="0.0.0.0", port=7583, debug=True)
