import uuid
import logging
from pathlib import Path
from typing import List
from fastapi import APIRouter, Depends, UploadFile, File, HTTPException, Request
from fastapi.responses import FileResponse
from sqlalchemy import select, func, desc
from sqlalchemy.ext.asyncio import AsyncSession
from app.database import get_db
from app.models import ClothingItem
from app.schemas import (
    ClothingItemResponse,
    ClothingItemList,
    ClothingItemUpdate,
    UploadResponse,
    BatchUploadResponse,
    ReanalyzeResponse,
    ConfirmWearableRequest,
    ConfirmWearableResponse,
)
from app.config import settings
from app.services.analysis_hints import label_from_filename

logger = logging.getLogger(__name__)
router = APIRouter(prefix="/api/items", tags=["items"])


async def _enqueue_analysis(request: Request, item_id: int) -> None:
    try:
        redis_pool = request.app.state.redis_pool
        if redis_pool:
            await redis_pool.enqueue_job("analyze_clothing", item_id)
            logger.info(f"Enqueued analysis job for item {item_id}")
            return
    except Exception as e:
        logger.error(f"Redis enqueue failed for item {item_id}: {e}")

    import asyncio
    from app.worker import run_local_job

    logger.warning(f"Using local background task for item {item_id}")
    asyncio.create_task(run_local_job(item_id))


async def _save_uploaded_file(file: UploadFile, db: AsyncSession) -> ClothingItem:
    if not file.content_type or not file.content_type.startswith("image/"):
        raise HTTPException(status_code=400, detail="Only image files are accepted")

    original_name = file.filename or "unknown"
    ext = Path(original_name).suffix or ".jpg"
    unique_name = f"{uuid.uuid4().hex}{ext}"
    upload_dir = Path(settings.UPLOAD_DIR)
    upload_dir.mkdir(parents=True, exist_ok=True)
    filepath = upload_dir / unique_name

    content = await file.read()
    with open(filepath, "wb") as f:
        f.write(content)

    item = ClothingItem(
        filename=original_name,
        filepath=str(filepath),
        status="pending",
        user_label=None,
    )
    db.add(item)
    await db.commit()
    await db.refresh(item)
    return item


@router.post("/upload", response_model=UploadResponse)
async def upload_item(
    request: Request,
    file: UploadFile = File(...),
    db: AsyncSession = Depends(get_db),
):
    """Upload a clothing image, save it, and enqueue AI analysis."""
    item = await _save_uploaded_file(file, db)
    await _enqueue_analysis(request, item.id)

    return UploadResponse(
        message="Image uploaded successfully. AI analysis queued.",
        item=ClothingItemResponse.model_validate(item),
    )


@router.post("/upload/batch", response_model=BatchUploadResponse)
async def upload_items_batch(
    request: Request,
    files: List[UploadFile] = File(...),
    db: AsyncSession = Depends(get_db),
):
    """Upload multiple images; AI uses each original filename as a classification hint."""
    if not files:
        raise HTTPException(status_code=400, detail="No files provided")
    if len(files) > 30:
        raise HTTPException(status_code=400, detail="Maximum 30 files per batch")

    items: List[ClothingItem] = []
    errors: List[str] = []

    for file in files:
        try:
            item = await _save_uploaded_file(file, db)
            items.append(item)
            await _enqueue_analysis(request, item.id)
        except HTTPException as e:
            errors.append(f"{file.filename}: {e.detail}")
        except Exception as e:
            errors.append(f"{file.filename}: {str(e)}")

    if not items:
        raise HTTPException(status_code=400, detail="No files uploaded; " + "; ".join(errors))

    return BatchUploadResponse(
        message=f"Uploaded {len(items)} item(s). AI analysis queued for each.",
        items=[ClothingItemResponse.model_validate(i) for i in items],
        uploaded=len(items),
        failed=len(errors),
        errors=errors,
    )


@router.get("", response_model=ClothingItemList)
async def list_items(
    skip: int = 0,
    limit: int = 50,
    db: AsyncSession = Depends(get_db),
):
    """List all clothing items with pagination."""
    # Count total
    count_result = await db.execute(select(func.count(ClothingItem.id)))
    total = count_result.scalar() or 0

    # Fetch items
    result = await db.execute(
        select(ClothingItem)
        .order_by(desc(ClothingItem.created_at))
        .offset(skip)
        .limit(limit)
    )
    items = result.scalars().all()

    return ClothingItemList(
        items=[ClothingItemResponse.model_validate(i) for i in items],
        total=total,
    )


@router.get("/{item_id}", response_model=ClothingItemResponse)
async def get_item(item_id: int, db: AsyncSession = Depends(get_db)):
    """Get a single clothing item by ID."""
    result = await db.execute(select(ClothingItem).where(ClothingItem.id == item_id))
    item = result.scalar_one_or_none()
    if not item:
        raise HTTPException(status_code=404, detail="Item not found")
    return ClothingItemResponse.model_validate(item)


@router.patch("/{item_id}", response_model=ClothingItemResponse)
async def update_item(
    item_id: int,
    body: ClothingItemUpdate,
    db: AsyncSession = Depends(get_db),
):
    """Update item name, category, and tags (manual corrections)."""
    result = await db.execute(select(ClothingItem).where(ClothingItem.id == item_id))
    item = result.scalar_one_or_none()
    if not item:
        raise HTTPException(status_code=404, detail="Item not found")

    if body.user_label is not None:
        item.user_label = body.user_label.strip() or None
    if body.clothing_type is not None:
        item.clothing_type = body.clothing_type.strip() or None
    if body.tags is not None:
        cleaned = [t.strip().lstrip("#") for t in body.tags if t and str(t).strip()]
        item.tags = cleaned

    await db.commit()
    await db.refresh(item)
    return ClothingItemResponse.model_validate(item)


@router.post("/{item_id}/confirm", response_model=ConfirmWearableResponse)
async def confirm_wearable_item(
    item_id: int,
    body: ConfirmWearableRequest,
    request: Request,
    db: AsyncSession = Depends(get_db),
):
    """User confirms or rejects an item flagged as non-clothing."""
    result = await db.execute(select(ClothingItem).where(ClothingItem.id == item_id))
    item = result.scalar_one_or_none()
    if not item:
        raise HTTPException(status_code=404, detail="Item not found")

    if item.status != "needs_confirmation":
        raise HTTPException(
            status_code=400,
            detail="This item is not awaiting confirmation",
        )

    if not body.confirmed:
        try:
            filepath = Path(item.filepath)
            if filepath.exists():
                filepath.unlink()
        except Exception as e:
            logger.error(f"Failed to delete file {item.filepath}: {e}")
        await db.delete(item)
        await db.commit()
        return ConfirmWearableResponse(
            message="Item removed from your wardrobe.",
            deleted=True,
        )

    raw = item.ai_raw_response if isinstance(item.ai_raw_response, dict) else {}
    raw["user_confirmed_wearable"] = True
    item.ai_raw_response = raw
    item.status = "pending"
    item.error_message = None
    await db.commit()

    await _enqueue_analysis(request, item_id)
    await db.refresh(item)

    return ConfirmWearableResponse(
        message="Thanks — re-analyzing as clothing from the photo.",
        item=ClothingItemResponse.model_validate(item),
        deleted=False,
    )


@router.post("/{item_id}/reanalyze", response_model=ReanalyzeResponse)
async def reanalyze_item(
    item_id: int,
    request: Request,
    db: AsyncSession = Depends(get_db),
):
    """Re-run AI analysis using the current name/tags as hints."""
    result = await db.execute(select(ClothingItem).where(ClothingItem.id == item_id))
    item = result.scalar_one_or_none()
    if not item:
        raise HTTPException(status_code=404, detail="Item not found")

    has_hint = bool(
        item.user_label
        or item.clothing_type
        or item.tags
        or label_from_filename(item.filename or "")
    )
    if not has_hint:
        raise HTTPException(
            status_code=400,
            detail="Set an item name or tags before re-analyzing so the AI has a hint.",
        )

    item.status = "pending"
    item.error_message = None
    await db.commit()

    await _enqueue_analysis(request, item_id)

    await db.refresh(item)
    return ReanalyzeResponse(
        message="Re-analysis queued. This page will update when finished.",
        item=ClothingItemResponse.model_validate(item),
    )


@router.delete("/{item_id}")
async def delete_item(item_id: int, db: AsyncSession = Depends(get_db)):
    """Delete a clothing item and its image file."""
    result = await db.execute(select(ClothingItem).where(ClothingItem.id == item_id))
    item = result.scalar_one_or_none()
    if not item:
        raise HTTPException(status_code=404, detail="Item not found")

    # Delete file
    try:
        filepath = Path(item.filepath)
        if filepath.exists():
            filepath.unlink()
    except Exception as e:
        logger.error(f"Failed to delete file {item.filepath}: {e}")

    await db.delete(item)
    await db.commit()
    return {"message": "Item deleted successfully"}


@router.get("/{item_id}/image")
async def get_item_image(item_id: int, db: AsyncSession = Depends(get_db)):
    """Serve the image file for a clothing item."""
    result = await db.execute(select(ClothingItem).where(ClothingItem.id == item_id))
    item = result.scalar_one_or_none()
    if not item:
        raise HTTPException(status_code=404, detail="Item not found")

    filepath = Path(item.filepath)
    if not filepath.exists():
        raise HTTPException(status_code=404, detail="Image file not found")

    # Determine content type
    ext = filepath.suffix.lower()
    content_types = {
        ".jpg": "image/jpeg",
        ".jpeg": "image/jpeg",
        ".png": "image/png",
        ".webp": "image/webp",
        ".gif": "image/gif",
    }
    content_type = content_types.get(ext, "application/octet-stream")

    return FileResponse(filepath, media_type=content_type)
