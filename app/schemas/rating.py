from datetime import datetime

from pydantic import BaseModel, ConfigDict, Field


class RatingCreate(BaseModel):
    value: int = Field(ge=1, le=5)


class RatingUpdate(BaseModel):
    value: int = Field(ge=1, le=5)


class RatingResponse(BaseModel):
    model_config = ConfigDict(from_attributes=True)

    id: int
    blog_id: int
    user_id: int
    value: int
    created_at: datetime
    updated_at: datetime


class RatingSummary(BaseModel):
    blog_id: int
    average_rating: float | None
    total_ratings: int
