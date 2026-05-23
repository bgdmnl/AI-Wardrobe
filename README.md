# 👗 Wardrobe Tracker

An AI-powered wardrobe management app that automatically analyzes and tags your clothing items. Upload a photo of any clothing piece and the app will identify its type, colors, material, pattern, season, and occasion using AI vision models.

---

## ✨ Features

- 📸 **Photo Upload** — Upload images of clothing items directly from your browser
- 🤖 **AI Analysis** — Automatically detects clothing type, colors, material, pattern, season, and occasion
- 🏷️ **Smart Tagging** — Each item gets a set of descriptive tags for easy browsing
- 🖼️ **Gallery View** — Browse your entire wardrobe in a clean card-based gallery
- 🔍 **Item Detail** — View full AI-generated details for any clothing item
- 🗑️ **Delete Items** — Remove items from your wardrobe
- ⚡ **Background Processing** — AI analysis runs in the background so uploads are instant
- 🔄 **Graceful Fallbacks** — Works without PostgreSQL (SQLite) and without Redis (local jobs)

---

## 🛠️ Tech Stack

### Frontend
- [Next.js 16](https://nextjs.org/) + React 19 + TypeScript
- [Tailwind CSS v4](https://tailwindcss.com/)
- [shadcn/ui](https://ui.shadcn.com/) component library
- [Sonner](https://sonner.emilkowal.ski/) for toast notifications

### Backend
- [FastAPI](https://fastapi.tiangolo.com/) (Python 3.12)
- [SQLAlchemy](https://www.sqlalchemy.org/) async ORM
- [PostgreSQL](https://www.postgresql.org/) (with automatic SQLite fallback)
- [Redis](https://redis.io/) + [arq](https://arq-docs.helpmanual.io/) for background job processing

### AI Providers (pluggable)
- **Mock** (default) — Instant realistic random tags, no external calls needed
- **Ollama** — Free local AI using LLaVA (vision) + LLaMA3 (text)
- **OpenAI** — GPT-4o for production-quality analysis

---

## 🚀 Getting Started

### Option 1 — Docker (Recommended)

Requires [Docker Desktop](https://www.docker.com/products/docker-desktop/).

```bash
git clone https://github.com/YOUR_USERNAME/YOUR_REPO_NAME.git
cd Wardrobe
docker compose up --build
```

- **Frontend** → http://localhost:3000
- **API Docs** → http://localhost:8000/docs

### Option 2 — Manual (Python + Node.js)

**Requirements:** Python 3.12+, Node.js 20+

**Terminal 1 — Backend:**
```bash
cd backend
python -m venv venv

# Windows
venv\Scripts\activate
# Mac/Linux
source venv/bin/activate

pip install -r requirements.txt
cp .env.example .env
uvicorn app.main:app --reload --host 0.0.0.0 --port 8000
```

**Terminal 2 — Frontend:**
```bash
cd frontend
npm install
npm run dev
```

Open **http://localhost:3000**

> PostgreSQL and Redis are optional — the app automatically falls back to SQLite and local background processing if they're not available.

---

## ⚙️ Configuration

Copy `backend/.env.example` to `backend/.env` and adjust as needed:

| Variable | Default | Description |
|---|---|---|
| `DATABASE_URL` | PostgreSQL | Falls back to SQLite automatically |
| `REDIS_HOST` | `localhost` | Falls back to local jobs if unavailable |
| `AI_PROVIDER` | `mock` | `mock`, `ollama`, or `openai` |
| `AI_VISION_MODEL` | `llava` | Vision model for image analysis |
| `AI_TEXT_MODEL` | `llama3` | Text model for description generation |
| `OPENAI_API_KEY` | *(empty)* | Required only if using OpenAI provider |

### Enabling Real AI

**With OpenAI:**
```env
AI_PROVIDER=openai
OPENAI_API_KEY=sk-your-key-here
AI_VISION_MODEL=gpt-4o
AI_TEXT_MODEL=gpt-4o
AI_ENDPOINTS=https://api.openai.com
```

**With Ollama (free, local):**
```bash
ollama pull llava
ollama pull llama3
```
```env
AI_PROVIDER=ollama
AI_ENDPOINTS=http://localhost:11434
AI_VISION_MODEL=llava
AI_TEXT_MODEL=llama3
```

---

## 📁 Project Structure

```
Wardrobe/
├── backend/
│   ├── app/
│   │   ├── main.py          # FastAPI app & startup
│   │   ├── config.py        # Settings & env vars
│   │   ├── database.py      # DB setup with SQLite fallback
│   │   ├── models.py        # SQLAlchemy models
│   │   ├── schemas.py       # Pydantic schemas
│   │   ├── worker.py        # arq background worker
│   │   ├── routes/
│   │   │   ├── items.py     # Upload, list, delete endpoints
│   │   │   └── health.py    # Health check endpoint
│   │   └── services/
│   │       ├── ai_service.py      # AI provider selector
│   │       ├── ai_providers.py    # Mock & OpenAI-compatible providers
│   │       └── ai_fallback.py     # Retry & fallback logic
│   ├── requirements.txt
│   └── Dockerfile
├── frontend/
│   ├── src/
│   │   ├── app/             # Next.js pages
│   │   ├── components/      # UI components
│   │   └── lib/
│   │       └── api.ts       # Backend API client
│   ├── package.json
│   └── Dockerfile
└── docker-compose.yml
```

---

## 📄 License

MIT
