"""Normalize AI vision output and apply to wardrobe items."""

from __future__ import annotations

from typing import Any, Dict, List, Optional

from app.models import ClothingItem

NON_WEARABLE_KEYWORDS = (
    "person", "face", "selfie", "landscape", "food", "pet", "dog", "cat",
    "car", "room", "furniture", "wall", "sky", "tree", "document", "receipt",
    "phone", "laptop", "book", "box", "package",
)


def parse_bool(value: Any, default: bool = True) -> bool:
    if isinstance(value, bool):
        return value
    if isinstance(value, str):
        return value.strip().lower() in ("true", "yes", "1", "wearable")
    if isinstance(value, (int, float)):
        return bool(value)
    return default


def build_display_name(
    clothing_type: Optional[str],
    colors: Optional[List[str]] = None,
    tags: Optional[List[str]] = None,
) -> str:
    """Human name from what is in the photo — never the raw filename."""
    ctype = (clothing_type or "clothing").replace("-", " ").strip()
    if not ctype or ctype.lower() in ("unknown", "clothing"):
        return "Clothing item"

    color = ""
    for c in colors or []:
        if c and str(c).lower() not in ("unknown", "n/a"):
            color = str(c).replace("-", " ").strip().title()
            break

    brand_tags = []
    for t in tags or []:
        tl = str(t).lower()
        if tl in ("jordan", "nike", "adidas", "puma", "reebok", "air", "force"):
            brand_tags.append(str(t).title())

    parts = []
    if color:
        parts.append(color)
    parts.append(ctype.title())
    name = " ".join(parts)
    if brand_tags:
        name = f"{' '.join(brand_tags[:2])} {name}".strip()
    return name


def normalize_analysis(raw: Dict[str, Any]) -> Dict[str, Any]:
    """Ensure consistent fields from any provider."""
    clothing_type = raw.get("clothing_type") or "unknown"
    colors = raw.get("colors") or []
    tags = raw.get("tags") or []
    is_wearable = parse_bool(raw.get("is_wearable"), default=True)

    ctype_lower = str(clothing_type).lower()
    if ctype_lower in ("unknown", "not clothing", "not_clothing", "none", "n/a"):
        is_wearable = False

    reason = raw.get("not_wearable_reason") or raw.get("rejection_reason")
    if not is_wearable and not reason:
        reason = "The image does not appear to show clothing or an outfit accessory."

    display_name = raw.get("display_name") or build_display_name(clothing_type, colors, tags)
    # Never use a name that looks like a bare filename
    if display_name and ("_" in display_name or display_name.endswith((".jpg", ".png"))):
        display_name = build_display_name(clothing_type, colors, tags)

    return {
        "clothing_type": clothing_type,
        "colors": colors,
        "pattern": raw.get("pattern") or "unknown",
        "material": raw.get("material") or "unknown",
        "season": raw.get("season") or ["all-season"],
        "occasion": raw.get("occasion") or ["casual"],
        "tags": tags,
        "description": raw.get("description") or "",
        "display_name": display_name,
        "is_wearable": is_wearable,
        "not_wearable_reason": reason,
        "raw_response": raw.get("raw_response"),
    }


def apply_analysis_to_item(item: ClothingItem, analysis: Dict[str, Any]) -> None:
    """Write AI results onto item; set status for confirmation or completed."""
    data = normalize_analysis(analysis)

    item.clothing_type = data["clothing_type"]
    item.colors = data["colors"]
    item.pattern = data["pattern"]
    item.material = data["material"]
    item.season = data["season"]
    item.occasion = data["occasion"]
    item.tags = data["tags"]
    item.description = data["description"]
    if data.get("raw_response") is not None:
        item.ai_raw_response = data["raw_response"]

    if not data["is_wearable"]:
        item.status = "needs_confirmation"
        item.user_label = None
        item.error_message = data["not_wearable_reason"]
        return

    item.user_label = data["display_name"]
    item.status = "completed"
    item.error_message = None
