```markdown
# 👗 Wardrobe Tracker

An AI-powered wardrobe management application that automatically analyzes and tags your clothing items. Upload a photo of any clothing piece and the app will identify its type, colors, material, pattern, season, and occasion using AI vision models. It also features an AI-driven outfit generator that creates stylish combinations directly from your digitized wardrobe.

---

## ✨ Features

- 📸 **Single & Batch Photo Upload** — Upload individual files or batch-upload up to 30 clothing images at once.
- 🤖 **AI Analysis Pipeline** — Automatically detects clothing type, colors, material, pattern, season, and occasion.
- 🔄 **Smart Classification Hints & Re-analysis** — The AI leverages original file names or manual user adjustments as contextual hints to refine tags during re-analysis.
- ⚠️ **Non-Clothing Content Detection** — Safeguards your wardrobe by flagging non-apparel items for a user manual confirmation review step before final parsing.
- 👚 **AI Outfit Suggestions** — Automatically blends your completed wardrobe items into cohesive top, bottom, footwear, outerwear, and accessory outfits tailored by occasion, season, or style rules.
- 🖼️ **Gallery View** — Browse your entire collection in a modern card-based layout featuring smart status tags and color preview badges.
- ⚡ **Asynchronous Background Tasks** — Analysis pipelines execute seamlessly in the background. Enqueues workloads via Redis or gracefully steps down to concurrent local in-memory tasks.
- 🔄 **Resilient Storage Architecture** — Operates natively on cloud-ready relational engines or runs locally via zero-configuration SQLite instances.

---

## 🛠️ Tech Stack

### Frontend
- **Framework:** Next.js 15+ (App Router) + React 19 + TypeScript
- **Styling:** Tailwind CSS v4
- **Components:** shadcn/ui (Primitive layer built on `@base-ui/react` and `lucide-react`)
- **Notifications:** Sonner

### Backend
- **Framework:** FastAPI (Python 3.12+)
- **ORM:** SQLAlchemy Async Engine (`aiosqlite`)
- **Database:** PostgreSQL (with automated fallback to a local `wardrobe.db` SQLite schema)
- **Job Broker:** arq + Redis (with transparent async in-memory task runner fallback if broker is missing)

### AI Middleware
- **Ollama** (Recommended & Native Local Default) — Vision evaluation via `llava` coupled with text generation via `llama3`.
- **OpenAI / OpenAI-Compatible** — Connects to structured enterprise endpoints or commercial cloud model APIs.
- **Mock** (Development Sandbox) — Generates local synthetic structures immediately for quick offline prototyping.

---

## 🚀 Getting Started

> 💡 **Important Setup Note:** The best and only reliable way to execute this project locally with production-grade AI analysis is using **Ollama**.

### Manual Execution Setup (Recommended for Local Development)

This app is structured as a decoupled full-stack architecture and should be run using two dedicated terminal sessions.

#### Terminal 1 — Backend Architecture

**Requirements:** Python 3.12+

1. Navigate to the backend directory and provision a virtual environment:
   ```bash
   cd backend
   python -m venv venv

```

2. Activate your local environment context:
* **Windows PowerShell:**
```powershell
.\venv\Scripts\Activate.ps1

```


* **Windows CMD:**
```cmd
.\venv\Scripts\activate.bat

```


* **macOS / Linux:**
```bash
source venv/bin/activate

```




3. Install the application dependencies:
```bash
pip install -r requirements.txt

```


4. Create your application configuration layout:
```bash
cp .env.example .env

```


5. Spin up the localized Uvicorn API runtime:
```bash
uvicorn app.main:app --reload --host 0.0.0.0 --port 8000

```



#### Terminal 2 — Frontend User Interface

**Requirements:** Node.js 20+

1. Navigate to the frontend workspace directory:
```bash
cd frontend

```


2. Install the node package dependencies:
```bash
npm install

```


3. Fire up the local development compilation pipeline:
```bash
npm run dev

```



* **User Portal View:** [http://localhost:3000](https://www.google.com/search?q=http://localhost:3000)
* **Interactive Open API Docs:** [http://localhost:8000/docs](https://www.google.com/search?q=http://localhost:8000/docs)
* **System Health JSON Status Node:** [http://localhost:8000/api/health](https://www.google.com/search?q=http://localhost:8000/api/health)

---

### Option 2 — Docker (Optional Execution Mode)

If you prefer containerized runtimes and have **Docker Desktop** installed, execute:

```bash
docker compose up --build

```

---

## ⚙️ Local AI Engine Configuration (Ollama)

To run the application locally without relying on paid or external cloud keys, configure Ollama on your machine:

1. Download and pull the required open-source Vision and Language models locally:
```bash
ollama pull llava
ollama pull llama3

```


2. Modify your `backend/.env` key mappings to target your local server instance:
```env
AI_PROVIDER=ollama
AI_ENDPOINTS=http://localhost:11434
AI_VISION_MODEL=llava
AI_TEXT_MODEL=llama3

```



---

## ⚙️ Alternative Environment Configurations

Copy `backend/.env.example` to `backend/.env` and adapt the pipeline configuration layer to fit your setup:

| Variable | System Fallback Mapping | Purpose / Operational Context |
| --- | --- | --- |
| `DATABASE_URL` | `sqlite+aiosqlite:///wardrobe.db` | Target PostgreSQL connection string; handles SQLite fallback gracefully |
| `REDIS_HOST` | `localhost` | Broker domain for arq worker background tasks; falls back to local execution |
| `REDIS_PORT` | `6379` | Active data connection port for the distributed job store |
| `UPLOAD_DIR` | `./uploads` | Persistent pathing root where uploaded wardrobe files reside |
| `AI_PROVIDER` | `mock` | Orchestration driver toggle: switch between `mock`, `ollama`, or `openai` |
| `AI_ENDPOINTS` | `http://localhost:11434` | Comma-separated fallback endpoints for the target model client |
| `AI_VISION_MODEL` | `llava` | Vision engine used to identify clothing visual characteristics |
| `AI_TEXT_MODEL` | `llama3` | Main completion model that structures JSON tags and metadata texts |
| `AI_TIMEOUT` | `60` | Hard cap processing deadline window for deep feature models |
| `AI_MAX_RETRIES` | `3` | Maximum backoff retry attempts for handling API connection issues |
| `OPENAI_API_KEY` | *(empty)* | Authorization header string; required only when using the `openai` driver |
| `CORS_ORIGINS` | `http://localhost:3000` | Whitelisted cross-origin domains allowed to consume endpoint outputs |

---

## 📁 Project Structure

```
Wardrobe/
├── backend/
│   ├── app/
│   │   ├── main.py              # FastAPI core lifecycle definition & CORS middleware
│   │   ├── config.py            # Pydantic BaseSettings management layer 
│   │   ├── database.py          # SQLAlchemy engine layer with dynamic Postgres-to-SQLite fallbacks
│   │   ├── models.py            # Relational database table schemas for apparel assets
│   │   ├── schemas.py           # Structured Pydantic validation nodes
│   │   ├── worker.py            # Async arq queue worker + in-memory task task-runner loop
│   │   ├── routes/
│   │   │   ├── health.py        # System health checks (Database, Redis, and AI availability statuses)
│   │   │   ├── items.py         # Image endpoints, single/batch uploads, re-analysis, reviews
│   │   │   └── outfits.py       # Combinatorial outfit generation orchestration nodes
│   │   └── services/
│   │       ├── ai_service.py     # AI driver selector engine
│   │       ├── ai_providers.py   # Implementations for local Ollama and OpenAI API connectors
│   │       ├── ai_fallback.py    # Resilience service managing endpoint retries & backoffs
│   │       ├── analysis_hints.py # Normalizes data inputs from files to supply model context
│   │       ├── analysis_result.py# Formats model schemas into system-readable attributes
│   │       └── outfit_service.py # Core logical framework managing outfit rule sets
│   ├── requirements.txt
│   └── Dockerfile
├── frontend/
│   ├── src/
│   │   ├── app/                 # Next.js App Router structural layout nodes
│   │   │   ├── item/[id]/       # Focused deep dive details view per apparel asset
│   │   │   ├── outfits/         # Interface for requesting and viewing outfit combinations
│   │   │   ├── upload/          # Upload manager workspace for single/batch files
│   │   │   └── page.tsx         # Wardrobe gallery dash template view
│   │   ├── components/          # UI Component architecture
│   │   │   ├── ui/              # Atomized base layout blocks (buttons, sheets, cards)
│   │   │   ├── gallery.tsx      # Wardrobe overview controller matching grid states
│   │   │   ├── upload-form.tsx  # Dynamic drag-and-drop interactive form interface
│   │   │   └── outfit-suggestions.tsx # Visual grid cards grouping outfit match layers
│   │   └── lib/
│   │       ├── api.ts           # Axios/Fetch integration mapping all client requests
│   │       └── utils.ts         # Utility methods for style definitions and Tailwind overrides
│   ├── package.json
│   └── Dockerfile
└── docker-compose.yml

```

---

## 📄 License

This project is open-source and available under the [MIT License](https://www.google.com/search?q=LICENSE).

```

```
