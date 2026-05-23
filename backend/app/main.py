import logging
from pathlib import Path
from contextlib import asynccontextmanager
from fastapi import FastAPI
from fastapi.middleware.cors import CORSMiddleware
from arq.connections import create_pool, RedisSettings
from app.config import settings
from app.database import init_db
from app.routes.items import router as items_router
from app.routes.health import router as health_router
from app.routes.outfits import router as outfits_router

# Configure logging
logging.basicConfig(
    level=logging.INFO,
    format="%(asctime)s [%(levelname)s] %(name)s: %(message)s",
)
logger = logging.getLogger(__name__)


@asynccontextmanager
async def lifespan(app: FastAPI):
    """Application startup and shutdown."""
    # Startup
    logger.info("Starting Wardrobe Tracker API...")

    # Init database tables
    await init_db()
    logger.info("Database tables initialized")

    # Create upload directory
    upload_dir = Path(settings.UPLOAD_DIR)
    upload_dir.mkdir(parents=True, exist_ok=True)
    logger.info(f"Upload directory: {upload_dir.absolute()}")

    # Create Redis pool for job enqueue
    try:
        redis_pool = await create_pool(
            RedisSettings(host=settings.REDIS_HOST, port=settings.REDIS_PORT)
        )
        app.state.redis_pool = redis_pool
        logger.info(f"Redis connected at {settings.REDIS_HOST}:{settings.REDIS_PORT}")
    except Exception as e:
        logger.error(f"Failed to connect to Redis: {e}")
        app.state.redis_pool = None

    logger.info(f"AI Provider: {settings.AI_PROVIDER}")
    logger.info("Wardrobe Tracker API ready!")

    yield

    # Shutdown
    if app.state.redis_pool:
        await app.state.redis_pool.close()
    logger.info("Wardrobe Tracker API shut down.")


app = FastAPI(
    title="Wardrobe Tracker API",
    description="AI-powered wardrobe management API",
    version="1.0.0",
    lifespan=lifespan,
)

# CORS
app.add_middleware(
    CORSMiddleware,
    allow_origins=settings.parsed_cors_origins,
    allow_credentials=True,
    allow_methods=["*"],
    allow_headers=["*"],
)

# Include routers
app.include_router(items_router)
app.include_router(health_router)
app.include_router(outfits_router)


@app.get("/")
async def root():
    return {
        "message": "Wardrobe Tracker API",
        "docs": "/docs",
        "health": "/api/health",
    }
