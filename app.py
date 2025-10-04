from flask import Flask, request, jsonify
from datetime import datetime, timedelta
import threading
import time

app = Flask(__name__)

# Speicher für Server-Daten
servers = {}
lock = threading.Lock()

# Automatisches Löschen alter Einträge (älter als 5 Min)
def cleanup():
    while True:
        time.sleep(60)
        with lock:
            cutoff = datetime.utcnow() - timedelta(minutes=5)
            to_delete = [sid for sid, data in servers.items() if data["last_seen"] < cutoff]
            for sid in to_delete:
                del servers[sid]

threading.Thread(target=cleanup, daemon=True).start()

# Endpunkt: Server-Daten senden (von Roblox)
@app.route("/report", methods=["POST"])
def report():
    data = request.json
    sid = data.get("server_id")
    mps = data.get("money_per_sec")
    if not sid or not isinstance(mps, (int, float)):
        return "Invalid", 400
    with lock:
        servers[sid] = {
            "money_per_sec": mps,
            "last_seen": datetime.utcnow()
        }
    return "OK", 200

# Endpunkt: Server abrufen (für dein Roblox-Script)
@app.route("/servers", methods=["GET"])
def get_servers():
    with lock:
        filtered = {sid: d["money_per_sec"] for sid, d in servers.items() if d["money_per_sec"] > 5_000_000}
    return jsonify(filtered)

if __name__ == "__main__":
    app.run(host="0.0.0.0", port=8080)