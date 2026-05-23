import json
import logging
import random
import re
from typing import Any, Dict, List, Optional

import httpx

from app.config import settings
from app.models import ClothingItem
from app.schemas import OutfitPiece, OutfitSuggestion
from app.services.ai_service import get_ai_provider
from app.services.ai_providers import MockProvider

logger = logging.getLogger(__name__)

OUTFIT_SYSTEM_PROMPT = """You are a fashion stylist AI. Given a user's wardrobe inventory, suggest complete outfits.

Return ONLY valid JSON with this exact structure:
{
  "outfits": [
    {
      "name": "short outfit title",
      "top": {"item_id": <number>, "clothing_type": "string", "colors": ["color"]},
      "bottom": {"item_id": <number>, "clothing_type": "string", "colors": ["color"]},
      "footwear": {"item_id": <number>, "clothing_type": "string", "colors": ["color"]},
      "outerwear": null or {"item_id": <number>, "clothing_type": "string", "colors": ["color"]},
      "accessory": null or {"item_id": <number>, "clothing_type": "string", "colors": ["color"]},
      "reasoning": "1-2 sentences explaining why this combination works"
    }
  ]
}

Rules:
- Generate exactly 3 outfits
- Each outfit must use real item_id values from the wardrobe list
- top, bottom, and footwear are required; outerwear is optional
- accessory is optional (e.g. scarf, necklace, cap, hat, belt, sunglasses, watch, bag, beanie, gloves). IMPORTANT: You MUST include at least one accessory in at least one of the 3 outfit suggestions if there are any accessories in the user's wardrobe.
- Consider color compatibility, occasion, season, and style
- Do not repeat the same item across multiple outfits when possible"""

TOP_TYPES = {
    "t-shirt", "polo", "tank-top", "sweater", "hoodie", "cardigan",
    "button-down shirt", "blouse", "top", "shirt",
}
BOTTOM_TYPES = {
    "jeans", "shorts", "skirt", "chinos", "joggers", "pants", "trousers",
}
FOOTWEAR_TYPES = {"sneakers", "boots", "sandals", "shoes", "loafers", "heels"}
OUTERWEAR_TYPES = {"jacket", "blazer", "coat", "vest", "parka", "windbreaker"}
ACCESSORY_TYPES = {
    "scarf", "necklace", "cap", "hat", "belt", "sunglasses", "glasses",
    "watch", "bag", "beanie", "gloves", "jewelry",
}


def _categorize_item(item: ClothingItem) -> str:
    clothing = (item.clothing_type or "").lower()
    if any(t in clothing for t in TOP_TYPES):
        return "top"
    if any(t in clothing for t in BOTTOM_TYPES):
        return "bottom"
    if any(t in clothing for t in FOOTWEAR_TYPES):
        return "footwear"
    if any(t in clothing for t in OUTERWEAR_TYPES):
        return "outerwear"
    if any(t in clothing for t in ACCESSORY_TYPES) or "accessory" in clothing:
        return "accessory"
    return "other"



def _item_to_piece(item: ClothingItem) -> OutfitPiece:
    return OutfitPiece(
        item_id=item.id,
        clothing_type=item.clothing_type or "unknown",
        colors=item.colors,
    )


def _format_wardrobe(items: List[ClothingItem]) -> str:
    lines = []
    for item in items:
        lines.append(
            json.dumps(
                {
                    "item_id": item.id,
                    "clothing_type": item.clothing_type,
                    "colors": item.colors or [],
                    "pattern": item.pattern,
                    "material": item.material,
                    "season": item.season or [],
                    "occasion": item.occasion or [],
                    "tags": item.tags or [],
                },
                ensure_ascii=False,
            )
        )
    return "\n".join(lines)


def _parse_outfit_json(text: str) -> Dict[str, Any]:
    try:
        return json.loads(text)
    except json.JSONDecodeError:
        match = re.search(r"```(?:json)?\s*([\s\S]*?)```", text)
        if match:
            return json.loads(match.group(1))
        match = re.search(r"\{[\s\S]*\}", text)
        if match:
            return json.loads(match.group(0))
        raise ValueError(f"Could not parse outfit JSON: {text[:200]}")


def _validate_outfits(
    raw_outfits: List[Dict[str, Any]], wardrobe: Dict[int, ClothingItem]
) -> List[OutfitSuggestion]:
    validated: List[OutfitSuggestion] = []

    for raw in raw_outfits[:3]:
        try:
            top_id = int(raw["top"]["item_id"])
            bottom_id = int(raw["bottom"]["item_id"])
            footwear_id = int(raw["footwear"]["item_id"])

            if top_id not in wardrobe or bottom_id not in wardrobe or footwear_id not in wardrobe:
                continue

            outerwear = None
            if raw.get("outerwear"):
                outer_id = int(raw["outerwear"]["item_id"])
                if outer_id in wardrobe:
                    outerwear = _item_to_piece(wardrobe[outer_id])

            accessory = None
            if raw.get("accessory"):
                acc_id = int(raw["accessory"]["item_id"])
                if acc_id in wardrobe:
                    accessory = _item_to_piece(wardrobe[acc_id])

            validated.append(
                OutfitSuggestion(
                    name=raw.get("name", "Styled Look"),
                    top=_item_to_piece(wardrobe[top_id]),
                    bottom=_item_to_piece(wardrobe[bottom_id]),
                    footwear=_item_to_piece(wardrobe[footwear_id]),
                    outerwear=outerwear,
                    accessory=accessory,
                    reasoning=raw.get("reasoning", "A balanced combination from your wardrobe."),
                )
            )
        except (KeyError, TypeError, ValueError) as e:
            logger.warning(f"Skipping invalid outfit entry: {e}")
            continue

    return validated



def _generate_mock_outfits(
    items: List[ClothingItem],
    occasion: str,
    season: str,
) -> List[OutfitSuggestion]:
    by_category: Dict[str, List[ClothingItem]] = {
        "top": [],
        "bottom": [],
        "footwear": [],
        "outerwear": [],
        "accessory": [],
        "other": [],
    }
    for item in items:
        by_category[_categorize_item(item)].append(item)

    tops = by_category["top"] or by_category["other"]
    bottoms = by_category["bottom"] or by_category["other"]
    footwear = by_category["footwear"] or by_category["other"]
    outerwear = by_category["outerwear"]
    accessories = by_category["accessory"]

    if not tops or not bottoms or not footwear:
        return []

    used_ids: set[int] = set()
    outfits: List[OutfitSuggestion] = []
    names = ["Everyday Classic", "Smart Casual", "Weekend Ready"]

    for index, name in enumerate(names):
        top = random.choice([i for i in tops if i.id not in used_ids] or tops)
        bottom = random.choice([i for i in bottoms if i.id not in used_ids] or bottoms)
        shoes = random.choice([i for i in footwear if i.id not in used_ids] or footwear)
        used_ids.update({top.id, bottom.id, shoes.id})

        outer = None
        if outerwear:
            candidate = random.choice(outerwear)
            if candidate.id not in used_ids:
                outer = _item_to_piece(candidate)
                used_ids.add(candidate.id)

        accessory = None
        if accessories:
            # Enforce at least one accessory for the first outfit if available, and add randomly for other outfits
            if index == 0 or random.random() > 0.5:
                candidate_acc = random.choice(accessories)
                if candidate_acc.id not in used_ids:
                    accessory = _item_to_piece(candidate_acc)
                    used_ids.add(candidate_acc.id)

        top_colors = ", ".join(top.colors or ["neutral"])
        bottom_colors = ", ".join(bottom.colors or ["neutral"])
        outfits.append(
            OutfitSuggestion(
                name=name,
                top=_item_to_piece(top),
                bottom=_item_to_piece(bottom),
                footwear=_item_to_piece(shoes),
                outerwear=outer,
                accessory=accessory,
                reasoning=(
                    f"A {occasion} {season} look pairing {top.clothing_type} ({top_colors}) "
                    f"with {bottom.clothing_type} ({bottom_colors}) and {shoes.clothing_type}"
                    f"{f' accessorized with {accessory.clothing_type}' if accessory else ''}."
                ),
            )
        )

    return outfits



async def _call_text_model(prompt: str) -> str:
    provider = get_ai_provider()
    if isinstance(provider, MockProvider):
        raise RuntimeError("mock_provider")

    endpoints = settings.parsed_ai_endpoints
    if settings.AI_PROVIDER.lower() == "openai" and not endpoints:
        endpoints = ["https://api.openai.com"]

    api_key = settings.AI_API_KEY or settings.OPENAI_API_KEY
    headers = {"Content-Type": "application/json"}
    if api_key:
        headers["Authorization"] = f"Bearer {api_key}"

    payload = {
        "model": settings.AI_TEXT_MODEL,
        "messages": [
            {"role": "system", "content": OUTFIT_SYSTEM_PROMPT},
            {"role": "user", "content": prompt},
        ],
        "temperature": 0.7,
        "max_tokens": 2000,
    }

    last_error: Optional[Exception] = None
    for endpoint in endpoints:
        url = f"{endpoint.rstrip('/')}/v1/chat/completions"
        try:
            async with httpx.AsyncClient(timeout=settings.AI_TIMEOUT) as client:
                resp = await client.post(url, json=payload, headers=headers)
                resp.raise_for_status()
                data = resp.json()
                return data["choices"][0]["message"]["content"]
        except Exception as e:
            last_error = e
            logger.warning(f"Outfit AI call failed on {endpoint}: {e}")

    raise last_error or RuntimeError("All AI endpoints failed for outfit suggestions")


async def suggest_outfits(
    items: List[ClothingItem],
    occasion: str = "casual",
    season: str = "summer",
    style: Optional[str] = None,
) -> List[OutfitSuggestion]:
    completed = [i for i in items if i.status == "completed" and i.clothing_type]
    if len(completed) < 3:
        return []

    wardrobe_map = {i.id: i for i in completed}
    style_line = f"\nPreferred style: {style}" if style else ""
    user_prompt = (
        f"Here are the user's wardrobe items (one JSON object per line):\n"
        f"{_format_wardrobe(completed)}\n\n"
        f"Generate 3 complete outfits for:\n"
        f"- occasion: {occasion}\n"
        f"- season: {season}"
        f"{style_line}"
    )

    try:
        if settings.AI_PROVIDER.lower() == "mock":
            raise RuntimeError("mock_provider")
        text = await _call_text_model(user_prompt)
        parsed = _parse_outfit_json(text)
        outfits = _validate_outfits(parsed.get("outfits", []), wardrobe_map)
        if outfits:
            return outfits
        logger.warning("AI returned no valid outfits, using mock fallback")
    except Exception as e:
        logger.info(f"Using mock outfit generator: {e}")

    return _generate_mock_outfits(completed, occasion, season)
