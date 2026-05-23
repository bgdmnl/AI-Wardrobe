import asyncio
import logging
from arq.connections import RedisSettings
from sqlalchemy import select
from app.config import settings
import app.database as db
from app.models import ClothingItem
from app.services.ai_service import analyze_clothing_item
from app.services.analysis_hints import build_analysis_hint
from app.services.analysis_result import apply_analysis_to_item

logger = logging.getLogger(__name__)

# One local analysis at a time (Ollama cannot handle many parallel vision jobs)
_local_analysis_lock = asyncio.Lock()


async def startup(ctx):
    """Worker startup: set up DB session factory."""
    logger.info("arq worker starting up...")
    ctx["session_factory"] = db.async_session


async def shutdown(ctx):
    """Worker shutdown: cleanup."""
    logger.info("arq worker shutting down...")


async def analyze_clothing(ctx, item_id: int):
    """Background job: analyze a clothing item with AI."""
    logger.info(f"Starting AI analysis for item {item_id}")
    session_factory = ctx["session_factory"]

    async with session_factory() as session:
        # Fetch item
        result = await session.execute(
            select(ClothingItem).where(ClothingItem.id == item_id)
        )
        item = result.scalar_one_or_none()

        if not item:
            logger.error(f"Item {item_id} not found in database")
            return

        # Mark as processing
        item.status = "processing"
        await session.commit()

        try:
            hint = build_analysis_hint(item)
            analysis = await analyze_clothing_item(item.filepath, hint=hint)
            apply_analysis_to_item(item, analysis)

            logger.info(
                f"AI analysis done for item {item_id}: status={item.status} "
                f"name={item.user_label} type={item.clothing_type}"
            )

        except Exception as e:
            logger.error(f"AI analysis failed for item {item_id}: {e}")
            item.status = "error"
            item.error_message = str(e)
            item.ai_raw_response = {"error": str(e), "type": type(e).__name__}

        await session.commit()


class WorkerSettings:
    """arq worker configuration."""
    functions = [analyze_clothing]
    redis_settings = RedisSettings(
        host=settings.REDIS_HOST,
        port=settings.REDIS_PORT,
    )
    on_startup = startup
    on_shutdown = shutdown
    max_jobs = 10
    job_timeout = 300


async def run_local_job(item_id: int):
    """Fallback runner for local development without Redis/arq."""
    logger.info(f"Queued local AI analysis for item {item_id}")
    await asyncio.sleep(0.5)
    async with _local_analysis_lock:
        ctx = {"session_factory": db.async_session}
        await analyze_clothing(ctx, item_id)

