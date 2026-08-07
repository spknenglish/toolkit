import random
import string
import time
import threading
from flask import Flask, request, jsonify, send_from_directory

app = Flask(__name__, static_folder="static", static_url_path="")

# ---------------------------------------------------------
# In-memory storage (no database).
# Data is lost on server restart - by design, per requirements.
# ---------------------------------------------------------
rooms = {}          # { code: { "messages": [ {id, sender, text, ts} ], "users": set() } }
lock = threading.Lock()

CODE_CHARS = string.ascii_uppercase + string.digits
CODE_LENGTH = 4


def generate_code():
    """Generate a unique 4-character alphanumeric code, e.g. A1D4."""
    while True:
        code = "".join(random.choices(CODE_CHARS, k=CODE_LENGTH))
        if code not in rooms:
            return code


def get_room(code):
    return rooms.get(code)


@app.route("/")
def index():
    return send_from_directory(app.static_folder, "index.html")


@app.route("/api/create", methods=["POST"])
def create_room():
    """Create a brand new chat room and return its code."""
    data = request.get_json(silent=True) or {}
    username = (data.get("username") or "Anonymous").strip()[:30] or "Anonymous"

    with lock:
        code = generate_code()
        rooms[code] = {
            "messages": [],
            "users": {username},
            "created_at": time.time(),
        }

    return jsonify({"ok": True, "code": code, "username": username})


@app.route("/api/join", methods=["POST"])
def join_room():
    """Join an existing chat room using its code."""
    data = request.get_json(silent=True) or {}
    code = (data.get("code") or "").strip().upper()
    username = (data.get("username") or "Anonymous").strip()[:30] or "Anonymous"

    if len(code) != CODE_LENGTH:
        return jsonify({"ok": False, "error": "Code must be 4 characters."}), 400

    with lock:
        room = get_room(code)
        if not room:
            return jsonify({"ok": False, "error": "Room not found. Check the code."}), 404
        room["users"].add(username)

    return jsonify({"ok": True, "code": code, "username": username})


@app.route("/api/send", methods=["POST"])
def send_message():
    """Send a message into a room."""
    data = request.get_json(silent=True) or {}
    code = (data.get("code") or "").strip().upper()
    username = (data.get("username") or "Anonymous").strip()[:30] or "Anonymous"
    text = (data.get("text") or "").strip()

    if not text:
        return jsonify({"ok": False, "error": "Empty message."}), 400
    if len(text) > 2000:
        text = text[:2000]

    with lock:
        room = get_room(code)
        if not room:
            return jsonify({"ok": False, "error": "Room not found."}), 404

        msg = {
            "id": len(room["messages"]) + 1,
            "sender": username,
            "text": text,
            "ts": time.time(),
        }
        room["messages"].append(msg)
        # keep memory bounded
        if len(room["messages"]) > 500:
            room["messages"] = room["messages"][-500:]

    return jsonify({"ok": True, "message": msg})


@app.route("/api/messages", methods=["GET"])
def get_messages():
    """Poll for messages in a room, optionally since a given message id."""
    code = (request.args.get("code") or "").strip().upper()
    since = request.args.get("since", default=0, type=int)

    with lock:
        room = get_room(code)
        if not room:
            return jsonify({"ok": False, "error": "Room not found."}), 404
        msgs = [m for m in room["messages"] if m["id"] > since]
        user_count = len(room["users"])

    return jsonify({"ok": True, "messages": msgs, "users": user_count})


@app.route("/api/room/<code>", methods=["GET"])
def room_exists(code):
    code = code.strip().upper()
    with lock:
        exists = code in rooms
    return jsonify({"ok": True, "exists": exists})


@app.errorhandler(404)
def not_found(e):
    return jsonify({"ok": False, "error": "Not found"}), 404


if __name__ == "__main__":
    import os
    port = int(os.environ.get("PORT", 5000))
    app.run(host="0.0.0.0", port=port, debug=False)
