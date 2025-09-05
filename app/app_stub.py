from flask import Flask, request, jsonify
app = Flask(__name__)

@app.get("/healthz")
def healthz():
    return jsonify({"ok": True})

@app.get("/version")
def version():
    return jsonify({"version":"1.0.0","commit":"stub","build_time":"2025-08-20T00:00:00Z"})

@app.post("/chat")
def chat():
    d = request.get_json(silent=True) or {}
    return jsonify({"ok": True, "echo": d.get("message","pong"), "request_id":"stub"})

wsgi_app = app  # gunicorn app_stub:wsgi_app
