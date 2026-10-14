from datetime import datetime

from pydantic import BaseModel, ConfigDict, Field


class BlogCreate(BaseModel):
    title: str = Field(..., min_length=3, max_length=200)
    content: str = Field(..., min_length=1)
    category_id: int = Field(..., gt=0)


class BlogUpdate(BaseModel):
    title: str | None = Field(default=None, min_length=3, max_length=200)
    content: str | None = Field(default=None, min_length=1)
    category_id: int | None = Field(default=None, gt=0)


class BlogResponse(BaseModel):
    id: int
    title: str
    content: str
    is_published: bool
    author_id: int
    category_id: int
    created_at: datetime
    updated_at: datetime

    model_config = ConfigDict(from_attributes=True)


class BlogPublishUpdate(BaseModel):
    is_published: bool
