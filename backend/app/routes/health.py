import logging
from fastapi import APIRouter, Request
from sqlalchemy import text
import app.database as db
from app.config import settings
from app.schemas import HealthResponse

logger = logging.getLogger(__name__)
router = APIRouter(prefix="/api", tags=["health"])


@router.get("/health", response_model=HealthResponse)
async def health_check(request: Request):
    """Check connectivity to DB, Redis, and AI provider."""
    db_status = "error"
    redis_status = "error"
    ai_status = "error"

    # Check DB
    if db.async_session is None:
        db_status = "initializing (wait for startup)"
    else:
        try:
            async with db.async_session() as session:
                await session.execute(text("SELECT 1"))
            if db.active_database_url and db.active_database_url.startswith("sqlite"):
                db_status = "ok (sqlite)"
            elif db.active_database_url and db.active_database_url.startswith("postgresql"):
                db_status = "ok (postgresql)"
            else:
                db_status = "ok"
        except Exception as e:
            db_status = f"error: {str(e)[:100]}"
            logger.error(f"Health check DB error: {e}")

    # Check Redis
    try:
        redis_pool = request.app.state.redis_pool
        if redis_pool:
            info = await redis_pool.info()
            redis_status = "ok"
        else:
            redis_status = "not connected (local worker fallback — OK)"
    except Exception as e:
        redis_status = f"error: {str(e)[:100]}"
        logger.error(f"Health check Redis error: {e}")

    # Check AI
    if settings.AI_PROVIDER == "mock":
        ai_status = "mock (no external AI needed)"
    else:
        try:
            import httpx
            endpoint = settings.parsed_ai_endpoints[0] if settings.parsed_ai_endpoints else ""
            if endpoint:
                async with httpx.AsyncClient(timeout=5.0) as client:
                    # Try Ollama-style health check
                    resp = await client.get(f"{endpoint}/api/tags")
                    if resp.status_code == 200:
                        ai_status = f"ok ({settings.AI_PROVIDER})"
                    else:
                        ai_status = f"reachable but returned {resp.status_code}"
            else:
                ai_status = "no endpoints configured"
        except Exception as e:
            ai_status = f"error: {str(e)[:100]}"
            logger.error(f"Health check AI error: {e}")

    return HealthResponse(
        db=db_status,
        redis=redis_status,
        ai=ai_status,
        ai_provider=settings.AI_PROVIDER.lower(),
    )
