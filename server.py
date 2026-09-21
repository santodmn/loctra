from datetime import datetime, timezone
from pathlib import Path
import json
import math
import os

from flask import Flask, jsonify, request, send_from_directory
from werkzeug.exceptions import RequestEntityTooLarge

BASE_DIR = Path(__file__).resolve().parent
LOG_FILE = BASE_DIR / "locations.jsonl"

app = Flask(__name__, static_folder=None)
app.config["MAX_CONTENT_LENGTH"] = 16 * 1024  # 16 KiB
app.config["JSON_SORT_KEYS"] = False


@app.after_request
def add_security_headers(response):
    response.headers["X-Content-Type-Options"] = "nosniff"
    response.headers["Referrer-Policy"] = "no-referrer"
    response.headers["Permissions-Policy"] = "geolocation=(self)"
    response.headers["Content-Security-Policy"] = (
        "default-src 'self'; "
        "script-src 'self' 'unsafe-inline'; "
        "style-src 'self' 'unsafe-inline'; "
        "img-src 'self' data:; "
        "connect-src 'self'; "
        "base-uri 'none'; "
        "form-action 'self'; "
        "frame-ancestors 'none'"
    )
    if request.path in {"/", "/api/location"}:
        response.headers["Cache-Control"] = "no-store"
    return response


@app.errorhandler(RequestEntityTooLarge)
def payload_too_large(_error):
    return jsonify({"ok": False, "error": "Richiesta troppo grande"}), 413


@app.get("/")
def home():
    return send_from_directory(BASE_DIR, "index.html")


@app.get("/health")
def health():
    return jsonify({"ok": True})


@app.post("/api/location")
def receive_location():
    if not request.is_json:
        return jsonify({"ok": False, "error": "Content-Type non valido"}), 415

    data = request.get_json(silent=True)
    if not isinstance(data, dict):
        return jsonify({"ok": False, "error": "JSON non valido"}), 400

    try:
        latitude = float(data["latitude"])
        longitude = float(data["longitude"])
        accuracy = float(data["accuracy_meters"])
    except (KeyError, TypeError, ValueError):
        return jsonify({"ok": False, "error": "Coordinate non valide"}), 400

    if not all(map(math.isfinite, (latitude, longitude, accuracy))):
        return jsonify({"ok": False, "error": "Valori non validi"}), 400
    if not -90 <= latitude <= 90:
        return jsonify({"ok": False, "error": "Latitudine fuori intervallo"}), 400
    if not -180 <= longitude <= 180:
        return jsonify({"ok": False, "error": "Longitudine fuori intervallo"}), 400
    if not 0 <= accuracy <= 100_000:
        return jsonify({"ok": False, "error": "Precisione non valida"}), 400

    timestamp = str(data.get("timestamp") or "")[:64]
    maps_url = f"https://maps.google.com/?q={latitude:.8f},{longitude:.8f}"

    record = {
        "received_at": datetime.now(timezone.utc).isoformat(),
        "latitude": latitude,
        "longitude": longitude,
        "accuracy_meters": accuracy,
        "timestamp": timestamp,
        "maps_url": maps_url,
    }

    # Copia locale temporanea. Su Render il filesystem del servizio non va
    # considerato persistente senza un Persistent Disk.
    try:
        with LOG_FILE.open("a", encoding="utf-8") as handle:
            handle.write(json.dumps(record, ensure_ascii=False) + "\n")
    except OSError as exc:
        print(f"Avviso: impossibile scrivere locations.jsonl: {exc}", flush=True)

    # Il dato utile resta visibile anche nei Logs di Render.
    print("NUOVA POSIZIONE:", flush=True)
    print(maps_url, flush=True)
    print(f"Precisione stimata: {accuracy:.0f} m", flush=True)

    return jsonify({
        "ok": True,
        "maps_url": maps_url,
        "accuracy_meters": accuracy,
    })


if __name__ == "__main__":
    port = int(os.environ.get("PORT", "8000"))
    app.run(host="0.0.0.0", port=port, debug=False)
