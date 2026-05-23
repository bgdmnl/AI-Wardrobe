from sqlalchemy import Column, Integer, String, Text, DateTime, JSON, func
from app.database import Base


class ClothingItem(Base):
    __tablename__ = "clothing_items"

    id = Column(Integer, primary_key=True, autoincrement=True)
    filename = Column(String(255), nullable=False)
    filepath = Column(String(500), nullable=False)
    status = Column(String(20), default="pending", nullable=False)
    user_label = Column(String(255), nullable=True)
    clothing_type = Column(String(100), nullable=True)
    colors = Column(JSON, nullable=True)
    pattern = Column(String(100), nullable=True)
    material = Column(String(100), nullable=True)
    season = Column(JSON, nullable=True)
    occasion = Column(JSON, nullable=True)
    tags = Column(JSON, nullable=True)
    description = Column(Text, nullable=True)
    ai_raw_response = Column(JSON, nullable=True)
    error_message = Column(Text, nullable=True)
    created_at = Column(DateTime(timezone=True), server_default=func.now())
    updated_at = Column(DateTime(timezone=True), server_default=func.now(), onupdate=func.now())
