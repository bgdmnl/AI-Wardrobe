# 👗 Wardrobe Tracker

An AI-powered wardrobe management application that automatically analyzes and tags clothing items. Users can upload images of clothing pieces, and the system identifies clothing type, colors, material, pattern, season, and occasion using AI vision models. It also includes an AI outfit generator that creates complete outfit combinations from the stored wardrobe.

---

## ✨ Features

- 📸 Single & Batch Upload (up to 30 images at once)
- 🤖 AI-powered clothing analysis (type, color, material, pattern, season, occasion)
- 🔄 Smart re-analysis using filename + user feedback hints
- ⚠️ Non-clothing detection with manual review flow
- 👚 AI outfit generator (top, bottom, shoes, accessories)
- 🖼️ Modern gallery view with tags and color previews
- ⚡ Background processing with Redis or local fallback
- 🔄 Automatic fallback to SQLite if PostgreSQL is not available

---

## 🛠️ Tech Stack

### Frontend
- Next.js 15+ (App Router), React 19, TypeScript
- Tailwind CSS v4
- shadcn/ui
- Sonner (notifications)

### Backend
- FastAPI (Python 3.12+)
- SQLAlchemy async ORM
- PostgreSQL (with SQLite fallback)
- arq + Redis (background jobs with fallback)

### AI Providers
- Ollama (recommended local setup: llava + llama3)
- OpenAI / compatible APIs
- Mock provider for development/testing

---

## 🚀 Getting Started

⚠️ Recommended: run locally using **Ollama + two terminals (backend + frontend)**

---

## ▶️ Manual Setup

### Backend (Terminal 1)

```bash
cd backend
python -m venv venv
```

Activate environment:

**Windows PowerShell**
```powershell
.\venv\Scripts\Activate.ps1
```

**Windows CMD**
```cmd
.\venv\Scripts\activate.bat
```

**macOS / Linux**
```bash
source venv/bin/activate
```

Install dependencies:

```bash
pip install -r requirements.txt
```

Create environment file:

```bash
cp .env.example .env
```

Run backend:

```bash
uvicorn app.main:app --reload --host 0.0.0.0 --port 8000
```

---

### Frontend (Terminal 2)

```bash
cd frontend
npm install
npm run dev
```

---

## 🌐 Access

- Frontend: http://localhost:3000  
- API Docs: http://localhost:8000/docs  
- Health Check: http://localhost:8000/api/health  

---

## 🐳 Docker (Optional)

```bash
docker compose up --build
```

---

## ⚙️ Ollama Setup (Recommended)

Install models:

```bash
ollama pull llava
ollama pull llama3
```

Configure environment:

```env
AI_PROVIDER=ollama
AI_ENDPOINTS=http://localhost:11434
AI_VISION_MODEL=llava
AI_TEXT_MODEL=llama3
```

---

## ⚙️ Environment Variables

- DATABASE_URL → PostgreSQL or SQLite fallback  
- REDIS_HOST → Background job system  
- AI_PROVIDER → mock / ollama / openai  
- AI_VISION_MODEL → vision model (llava)  
- AI_TEXT_MODEL → text model (llama3)  
- OPENAI_API_KEY → required only for OpenAI  

---

## 📁 Project Structure

backend/
  app/
    main.py
    config.py
    database.py
    models.py
    schemas.py
    worker.py
    routes/
    services/

frontend/
  src/
    app/
    components/
    lib/

docker-compose.yml

---

## 📄 License

MIT
