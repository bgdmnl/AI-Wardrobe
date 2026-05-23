import logging
from typing import Dict, Any, Optional
from app.config import settings
from app.services.ai_providers import MockProvider, AIProvider
from app.services.ai_fallback import AIFallbackService

logger = logging.getLogger(__name__)


def get_ai_provider() -> AIProvider | AIFallbackService:
    """Return the appropriate AI provider based on configuration."""
    provider_name = settings.AI_PROVIDER.lower()

    if provider_name == "mock":
        logger.info("Using MockProvider (no external AI)")
        return MockProvider()

    elif provider_name in ("ollama", "openai"):
        api_key = settings.AI_API_KEY
        if provider_name == "openai" and settings.OPENAI_API_KEY:
            api_key = settings.OPENAI_API_KEY

        endpoints = settings.parsed_ai_endpoints
        if provider_name == "openai" and not endpoints:
            endpoints = ["https://api.openai.com"]

        logger.info(
            f"Using {provider_name} provider with endpoints: {endpoints}"
        )

        return AIFallbackService(
            endpoints=endpoints,
            vision_model=settings.AI_VISION_MODEL,
            text_model=settings.AI_TEXT_MODEL,
            api_key=api_key,
            timeout=settings.AI_TIMEOUT,
            max_retries=settings.AI_MAX_RETRIES,
        )

    else:
        logger.warning(f"Unknown AI provider '{provider_name}', falling back to mock")
        return MockProvider()


async def analyze_clothing_item(
    image_path: str, hint: Optional[str] = None
) -> Dict[str, Any]:
    """Convenience function: get the configured provider and analyze."""
    provider = get_ai_provider()
    return await provider.analyze(image_path, hint=hint)
