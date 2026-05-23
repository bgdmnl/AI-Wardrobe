import json
import logging
import base64
import mimetypes
from abc import ABC, abstractmethod
from typing import Dict, Any, Optional
import httpx

from app.services.analysis_hints import mock_analysis_from_hint, mock_analysis_without_hint
from app.services.analysis_result import normalize_analysis, parse_bool

logger = logging.getLogger(__name__)

# ──────────────────────────────────────────────
# Base interface
# ──────────────────────────────────────────────

class AIProvider(ABC):
    @abstractmethod
    async def analyze(
        self, image_path: str, hint: Optional[str] = None
    ) -> Dict[str, Any]:
        """Analyze a clothing image and return structured tags + description."""
        ...


# ──────────────────────────────────────────────
# Mock Provider – works out of the box, zero deps
# ──────────────────────────────────────────────

CLOTHING_TYPES = [
    "t-shirt", "jeans", "dress", "jacket", "sneakers", "hoodie", "skirt",
    "blazer", "shorts", "sweater", "coat", "polo", "cardigan", "tank-top",
    "joggers", "button-down shirt", "chinos", "boots", "sandals",
]
COLORS = [
    "black", "white", "navy", "gray", "red", "blue", "green", "beige",
    "brown", "pink", "olive", "burgundy", "cream", "teal", "coral",
]
PATTERNS = [
    "solid", "striped", "plaid", "floral", "geometric", "abstract",
    "polka-dot", "checkered", "paisley", "color-block",
]
MATERIALS = [
    "cotton", "denim", "polyester", "wool", "silk", "leather", "linen",
    "nylon", "cashmere", "fleece", "canvas", "jersey",
]
SEASONS = ["spring", "summer", "fall", "winter", "all-season"]
OCCASIONS = [
    "casual", "formal", "business", "athletic", "evening", "everyday",
    "weekend", "date-night", "outdoor",
]
ADJECTIVES = [
    "comfortable", "trendy", "classic", "versatile", "lightweight", "warm",
    "breathable", "waterproof", "slim-fit", "oversized", "relaxed-fit",
    "tailored", "cozy", "elegant", "sporty", "minimalist", "bold",
]


class MockProvider(AIProvider):
    """No vision — uses owner label/tags when provided, otherwise asks user to label."""

    async def analyze(
        self, image_path: str, hint: Optional[str] = None
    ) -> Dict[str, Any]:
        if hint and hint.strip():
            return mock_analysis_from_hint(hint)
        return mock_analysis_without_hint()
        # normalize_analysis applied inside mock helpers


# ──────────────────────────────────────────────
# OpenAI-compatible Provider (Ollama / OpenAI / LM Studio / etc.)
# ──────────────────────────────────────────────

VISION_SYSTEM_PROMPT = """You are a clothing analysis assistant. Look at the IMAGE.

Return ONLY valid JSON:
{
  "is_wearable": true or false,
  "display_name": "short name for what you SEE (e.g. Black Jordan 4 Sneakers) — NEVER the filename",
  "clothing_type": "garment type (t-shirt, jeans, sneakers, jacket, belt, watch, etc.)",
  "colors": ["color strings from the image"],
  "pattern": "solid, striped, etc.",
  "material": "cotton, denim, leather, etc.",
  "season": ["spring", "summer", etc.],
  "occasion": ["casual", "formal", etc.],
  "tags": ["descriptive tags including brand if visible"],
  "not_wearable_reason": "only if is_wearable is false — why (person, food, room, etc.)"
}

Rules:
- is_wearable: true only for clothing or outfit accessories (shoes, belt, bag, hat, watch, jewelry).
- is_wearable: false for people, faces, pets, food, rooms, cars, random objects.
- display_name MUST come from the garment visible in the photo, NOT from any filename hint.
- Filename hints (if provided) may help classification only — never copy them as display_name.
- clothing_type must match what is actually in the image."""

DESCRIPTION_SYSTEM_PROMPT = """You are a fashion assistant. Write a brief, natural 1-2 sentence
description of a clothing item based on the provided tags. Be conversational and helpful."""


class OpenAICompatibleProvider(AIProvider):
    """Hits any OpenAI-compatible /v1/chat/completions endpoint."""

    def __init__(self, endpoint: str, vision_model: str, text_model: str,
                 api_key: str = "", timeout: int = 60):
        self.endpoint = endpoint.rstrip("/")
        self.vision_model = vision_model
        self.text_model = text_model
        self.api_key = api_key
        self.timeout = timeout

    def _headers(self) -> dict:
        headers = {"Content-Type": "application/json"}
        if self.api_key:
            headers["Authorization"] = f"Bearer {self.api_key}"
        return headers

    async def analyze(
        self, image_path: str, hint: Optional[str] = None
    ) -> Dict[str, Any]:
        # Step 1: Vision model → structured tags
        with open(image_path, "rb") as f:
            image_b64 = base64.b64encode(f.read()).decode()

        mime_type = mimetypes.guess_type(image_path)[0] or "image/jpeg"

        user_text = "Analyze the clothing or accessory in this image. Return JSON:"
        if hint and hint.strip():
            user_text += f"\n\nOptional context (filename hint only, not the name to output):\n{hint.strip()}"

        vision_payload = {
            "model": self.vision_model,
            "messages": [
                {"role": "system", "content": VISION_SYSTEM_PROMPT},
                {
                    "role": "user",
                    "content": [
                        {"type": "text", "text": user_text},
                        {
                            "type": "image_url",
                            "image_url": {"url": f"data:{mime_type};base64,{image_b64}"},
                        },
                    ],
                },
            ],
            "temperature": 0.2,
            "max_tokens": 1000,
        }

        async with httpx.AsyncClient(timeout=self.timeout) as client:
            resp = await client.post(
                f"{self.endpoint}/v1/chat/completions",
                json=vision_payload,
                headers=self._headers(),
            )
            resp.raise_for_status()
            vision_raw = resp.json()

        vision_text = vision_raw["choices"][0]["message"]["content"]
        # Try to parse JSON from the response (handle markdown code blocks)
        try:
            tags = json.loads(vision_text)
        except json.JSONDecodeError:
            # Try extracting JSON from markdown code block
            import re
            json_match = re.search(r"```(?:json)?\s*([\s\S]*?)```", vision_text)
            if json_match:
                tags = json.loads(json_match.group(1))
            else:
                raise ValueError(f"Could not parse JSON from vision response: {vision_text[:200]}")

        if not parse_bool(tags.get("is_wearable"), default=True):
            return normalize_analysis({
                **tags,
                "description": tags.get("not_wearable_reason") or "",
                "raw_response": {"vision": vision_raw},
            })

        # Step 2: Text model → description
        desc_payload = {
            "model": self.text_model,
            "messages": [
                {"role": "system", "content": DESCRIPTION_SYSTEM_PROMPT},
                {
                    "role": "user",
                    "content": f"Write a brief description for this clothing item based on these tags: {json.dumps(tags)}",
                },
            ],
            "temperature": 0.7,
            "max_tokens": 200,
        }

        async with httpx.AsyncClient(timeout=self.timeout) as client:
            resp = await client.post(
                f"{self.endpoint}/v1/chat/completions",
                json=desc_payload,
                headers=self._headers(),
            )
            resp.raise_for_status()
            desc_raw = resp.json()

        description = desc_raw["choices"][0]["message"]["content"]

        merged = {
            **tags,
            "description": description,
            "raw_response": {"vision": vision_raw, "description": desc_raw},
        }
        return normalize_analysis(merged)
