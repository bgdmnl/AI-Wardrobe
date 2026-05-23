import asyncio
import logging
from typing import List, Dict, Any, Optional
from app.services.ai_providers import OpenAICompatibleProvider

logger = logging.getLogger(__name__)


class AIFallbackService:
    """Tries multiple endpoints in order with retries and exponential backoff."""

    def __init__(
        self,
        endpoints: List[str],
        vision_model: str,
        text_model: str,
        api_key: str = "",
        timeout: int = 60,
        max_retries: int = 3,
    ):
        self.endpoints = endpoints
        self.vision_model = vision_model
        self.text_model = text_model
        self.api_key = api_key
        self.timeout = timeout
        self.max_retries = max_retries

    async def analyze(
        self, image_path: str, hint: Optional[str] = None
    ) -> Dict[str, Any]:
        all_errors = []

        for endpoint in self.endpoints:
            provider = OpenAICompatibleProvider(
                endpoint=endpoint,
                vision_model=self.vision_model,
                text_model=self.text_model,
                api_key=self.api_key,
                timeout=self.timeout,
            )

            for attempt in range(1, self.max_retries + 1):
                try:
                    logger.info(
                        f"AI analysis attempt {attempt}/{self.max_retries} "
                        f"on endpoint {endpoint}"
                    )
                    result = await provider.analyze(image_path, hint=hint)
                    logger.info(f"AI analysis succeeded on {endpoint}")
                    return result

                except Exception as e:
                    error_msg = f"Endpoint {endpoint}, attempt {attempt}: {str(e)}"
                    logger.warning(error_msg)
                    all_errors.append(error_msg)

                    if attempt < self.max_retries:
                        backoff = 2 ** (attempt - 1)  # 1s, 2s, 4s
                        logger.info(f"Retrying in {backoff}s...")
                        await asyncio.sleep(backoff)

            logger.error(f"All retries exhausted for endpoint {endpoint}")

        error_summary = "; ".join(all_errors)
        raise Exception(
            f"AI analysis failed on all endpoints after all retries. Errors: {error_summary}"
        )
