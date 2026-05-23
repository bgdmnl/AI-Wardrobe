"""Build analysis hints from user labels/tags and mock keyword parsing."""

from __future__ import annotations

import re
from typing import Any, Dict, List, Optional

from app.models import ClothingItem

NON_WEARABLE_KEYWORDS = (
    "person", "face", "selfie", "landscape", "food", "pet", "car", "room", "furniture",
)

COLOR_WORDS = [
    "black", "white", "navy", "gray", "grey", "red", "blue", "green", "beige",
    "brown", "pink", "olive", "burgundy", "cream", "teal", "coral", "dark blue",
    "light blue",
]

TYPE_RULES: List[tuple[tuple[str, ...], str, str]] = [
    (("jordan", "air force", "airforce", "sneaker", "trainer", "shoe"), "sneakers", "canvas"),
    (("jean", "denim"), "jeans", "denim"),
    (("chino", "trouser", "pant"), "chinos", "cotton"),
    (("hoodie", "sweatshirt"), "hoodie", "fleece"),
    (("sweater", "jumper", "pullover"), "sweater", "wool"),
    (("tank", "vest"), "tank-top", "cotton"),
    (("t-shirt", "tshirt", "tee", "shirt"), "t-shirt", "cotton"),
    (("blazer", "jacket", "coat"), "jacket", "wool"),
    (("short",), "shorts", "cotton"),
    (("dress",), "dress", "cotton"),
    (("skirt",), "skirt", "cotton"),
    (("polo",), "polo", "cotton"),
    (("boot",), "boots", "leather"),
    (("sandal",), "sandals", "rubber"),
    (("gym", "athletic", "sport", "workout"), "t-shirt", "polyester"),
]


def label_from_filename(filename: str) -> str:
    """Turn 'black_jordan_4_sneakers.jpg' into 'Black Jordan 4 Sneakers'."""
    stem = filename.rsplit("/", 1)[-1]
    stem = stem.rsplit("\\", 1)[-1]
    if "." in stem:
        stem = stem.rsplit(".", 1)[0]
    stem = re.sub(r"^(img|image|photo|pic|dsc|dscn|wp|screenshot)[-_]?\d*$", "", stem, flags=re.I)
    stem = re.sub(r"[-_]+", " ", stem)
    stem = re.sub(r"\s+", " ", stem).strip()
    if not stem:
        return ""
    return stem.title()


def build_analysis_hint(item: ClothingItem, user_confirmed: bool = False) -> Optional[str]:
    parts: List[str] = []
    file_hint = label_from_filename(item.filename) if item.filename else ""
    if file_hint:
        parts.append(
            f"Optional filename hint only (do NOT use as display_name): {file_hint}"
        )
    if user_confirmed or (
        item.ai_raw_response
        and isinstance(item.ai_raw_response, dict)
        and item.ai_raw_response.get("user_confirmed_wearable")
    ):
        parts.append(
            "The user confirmed this photo shows wearable clothing or an outfit accessory. "
            "Identify from the image."
        )
    if item.user_label and item.user_label.strip():
        parts.append(
            f"Owner override name (for re-analysis only, prefer vision): {item.user_label.strip()}"
        )
    if item.tags:
        parts.append(f"Owner tags: {', '.join(str(t) for t in item.tags)}")
    parts.append(
        "Look at the IMAGE first. Filename is only a weak hint. "
        "display_name must describe what you SEE, not the file name."
    )
    return "\n".join(parts) if parts else None


def mock_analysis_from_hint(hint: str) -> Dict[str, Any]:
    """Keyword-based tags when mock AI is active (no vision)."""
    h = hint.lower()
    clothing_type = "clothing"
    material = "cotton"

    for keywords, ctype, mat in TYPE_RULES:
        if any(k in h for k in keywords):
            clothing_type = ctype
            material = mat
            break

    colors: List[str] = []
    if "dark blue" in h:
        colors.append("navy")
    if "light blue" in h:
        colors.append("blue")
    for c in COLOR_WORDS:
        if c in ("dark blue", "light blue"):
            continue
        if re.search(rf"\b{re.escape(c)}\b", h) and c not in colors:
            colors.append("gray" if c == "grey" else c)

    words = re.findall(r"[a-z0-9]+", h)
    tag_set = {clothing_type}
    for w in words:
        if len(w) > 2 and w not in colors:
            tag_set.add(w)
    tags = list(tag_set)[:8]

    if "oversized" in h:
        tags.append("oversized")
    if "baggy" in h:
        tags.append("baggy")

    from app.services.analysis_result import build_display_name, normalize_analysis

    is_wearable = not any(k in h for k in NON_WEARABLE_KEYWORDS)
    if clothing_type == "clothing" and not any(
        k in h for k in ("jean", "shirt", "shoe", "sneaker", "jacket", "hoodie", "dress", "skirt", "boot")
    ):
        is_wearable = False

    color_text = ", ".join(colors) if colors else "neutral"
    raw = {
        "clothing_type": clothing_type,
        "colors": colors or ["unknown"],
        "pattern": "solid",
        "material": material,
        "season": ["all-season"],
        "occasion": ["athletic"] if any(x in h for x in ("gym", "sport", "workout")) else ["casual"],
        "tags": tags,
        "is_wearable": is_wearable,
        "display_name": build_display_name(clothing_type, colors, tags),
        "description": (
            f"Identified as {clothing_type} in {color_text} from image context."
        ),
        "raw_response": {"provider": "mock", "hint_used": True},
    }
    if not is_wearable:
        raw["not_wearable_reason"] = "Could not confirm clothing in image (mock mode — use Ollama for vision)."
    return normalize_analysis(raw)


def mock_analysis_without_hint() -> Dict[str, Any]:
    from app.services.analysis_result import normalize_analysis

    return normalize_analysis({
        "clothing_type": "unknown",
        "colors": [],
        "pattern": "unknown",
        "material": "unknown",
        "season": ["all-season"],
        "occasion": ["casual"],
        "tags": [],
        "is_wearable": False,
        "not_wearable_reason": "No vision available — configure Ollama or confirm manually.",
        "description": "Configure AI_PROVIDER=ollama for photo analysis.",
        "raw_response": {"provider": "mock", "hint_used": False},
    })
