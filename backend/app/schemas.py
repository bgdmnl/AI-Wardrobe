from pydantic import BaseModel, ConfigDict
from typing import List, Optional
from datetime import datetime


class ClothingItemResponse(BaseModel):
    id: int
    filename: str
    filepath: str
    status: str
    user_label: Optional[str] = None
    clothing_type: Optional[str] = None
    colors: Optional[List[str]] = None
    pattern: Optional[str] = None
    material: Optional[str] = None
    season: Optional[List[str]] = None
    occasion: Optional[List[str]] = None
    tags: Optional[List[str]] = None
    description: Optional[str] = None
    error_message: Optional[str] = None
    created_at: Optional[datetime] = None
    updated_at: Optional[datetime] = None

    model_config = ConfigDict(from_attributes=True)


class ClothingItemList(BaseModel):
    items: List[ClothingItemResponse]
    total: int


class ClothingItemUpdate(BaseModel):
    user_label: Optional[str] = None
    clothing_type: Optional[str] = None
    tags: Optional[List[str]] = None


class ReanalyzeResponse(BaseModel):
    message: str
    item: ClothingItemResponse


class ConfirmWearableRequest(BaseModel):
    confirmed: bool


class ConfirmWearableResponse(BaseModel):
    message: str
    item: Optional[ClothingItemResponse] = None
    deleted: bool = False


class UploadResponse(BaseModel):
    message: str
    item: ClothingItemResponse


class BatchUploadResponse(BaseModel):
    message: str
    items: List[ClothingItemResponse]
    uploaded: int
    failed: int
    errors: List[str]


class HealthResponse(BaseModel):
    db: str
    redis: str
    ai: str
    ai_provider: str


class OutfitSuggestRequest(BaseModel):
    occasion: str = "casual"
    season: str = "summer"
    style: Optional[str] = None


class OutfitPiece(BaseModel):
    item_id: int
    clothing_type: str
    colors: Optional[List[str]] = None


class OutfitSuggestion(BaseModel):
    name: str
    top: OutfitPiece
    bottom: OutfitPiece
    footwear: OutfitPiece
    outerwear: Optional[OutfitPiece] = None
    accessory: Optional[OutfitPiece] = None
    reasoning: str


class OutfitSuggestResponse(BaseModel):
    outfits: List[OutfitSuggestion]
    wardrobe_count: int
