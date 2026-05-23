import logging

from fastapi import APIRouter, Depends, HTTPException
from sqlalchemy import select
from sqlalchemy.ext.asyncio import AsyncSession

from app.database import get_db
from app.models import ClothingItem
from app.schemas import OutfitSuggestRequest, OutfitSuggestResponse
from app.services.outfit_service import suggest_outfits

logger = logging.getLogger(__name__)
router = APIRouter(prefix="/api/outfits", tags=["outfits"])


@router.post("/suggest", response_model=OutfitSuggestResponse)
async def suggest_outfit_combinations(
    body: OutfitSuggestRequest,
    db: AsyncSession = Depends(get_db),
):
    """Generate AI outfit suggestions from the user's analyzed wardrobe."""
    result = await db.execute(
        select(ClothingItem).where(ClothingItem.status == "completed")
    )
    items = list(result.scalars().all())
    completed_count = len(items)

    if completed_count < 3:
        raise HTTPException(
            status_code=400,
            detail=(
                f"Need at least 3 analyzed clothing items for outfit suggestions. "
                f"You have {completed_count}."
            ),
        )

    outfits = await suggest_outfits(
        items=items,
        occasion=body.occasion,
        season=body.season,
        style=body.style,
    )

    if not outfits:
        raise HTTPException(
            status_code=400,
            detail=(
                "Could not generate outfits. Ensure your wardrobe has tops, "
                "bottoms, and footwear with completed AI analysis."
            ),
        )

    return OutfitSuggestResponse(
        outfits=outfits,
        wardrobe_count=completed_count,
    )
