# ChatCode — Simple Room-Code Chat App

A minimal WhatsApp-style chat app. No database — everything is stored
**in server memory** (rooms/messages) and in the **browser's localStorage**
(your session + local message history), exactly as requested.

## How it works

- One person clicks **Create New Chat** → gets a 4-character code (e.g. `A1D4`).
- They share that code with the other person.
- The other person clicks **Join Chat**, enters the code → both are now in the same room.
- Messages are sent to the Flask backend and fetched via polling (every 2s) — no
  external dependencies, no WebSocket server needed, works anywhere.
- Login info (your name + room code) and the chat log are cached in the browser's
  `localStorage`, so refreshing the page resumes your session automatically.

## Project structure

```
chatapp/
├── app.py              # Flask backend (in-memory rooms, REST API)
├── static/
│   └── index.html       # All-in-one frontend (HTML+CSS+JS, WhatsApp-style UI)
├── requirements.txt      # Flask + gunicorn
├── Procfile              # For Render/Heroku-style process declaration
├── render.yaml            # Render Blueprint (one-click deploy config)
└── README.md
```

## Run locally

```bash
pip install -r requirements.txt
python app.py
```

Then open **http://localhost:5000** in two different browser tabs (or two
devices) to simulate two users chatting.

For a production-style run locally:

```bash
gunicorn app:app --bind 0.0.0.0:5000
```

## Deploy to Render

### Option A — Blueprint (recommended)
1. Push this project to a GitHub repo.
2. In Render, click **New → Blueprint**, point it at your repo. Render will read
   `render.yaml` and configure everything automatically.
3. Click **Apply** — done. Your app will be live at `https://<your-service>.onrender.com`.

### Option B — Manual Web Service
1. Push this project to GitHub.
2. In Render, click **New → Web Service**, connect the repo.
3. Set:
   - **Build Command:** `pip install -r requirements.txt`
   - **Start Command:** `gunicorn app:app --bind 0.0.0.0:$PORT`
4. Deploy.

No environment variables or database setup are required.

## API Endpoints (backend)

| Method | Endpoint             | Description                              |
|--------|-----------------------|-------------------------------------------|
| POST   | `/api/create`          | Create a room, returns a 4-char code      |
| POST   | `/api/join`             | Join a room by code                      |
| POST   | `/api/send`             | Send a message `{code, username, text}`  |
| GET    | `/api/messages?code=&since=` | Poll for new messages              |
| GET    | `/api/room/<code>`      | Check if a room code exists              |

## Notes / limitations (by design, per requirements)

- **No database** — all chat rooms live in the Flask process memory. If the
  server restarts (e.g. free-tier Render sleeps/redeploys), existing room
  codes and messages on the server are cleared. Locally cached messages in
  each browser's `localStorage` remain, but a room's code becomes invalid
  server-side until a new one is created.
- Uses simple polling instead of WebSockets to keep the backend dependency-free
  and easy to deploy on Render's free tier.
- Designed for two (or a few) people per room code — it's a lightweight demo,
  not meant for large-scale group chat.
