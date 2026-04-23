from pydantic import BaseModel
from typing import Optional
from datetime import datetime


class ProfileCreate(BaseModel):
    name: str


class ProfileResponse(BaseModel):
    id: str
    name: str
    gender: Optional[str]
    gender_probability: Optional[float]
    sample_size: Optional[int]
    age: Optional[int]
    age_group: Optional[str]
    country_id: Optional[str]
    country_name: Optional[str]
    country_probability: Optional[float]
    created_at: datetime

    class Config:
        from_attributes = True


class ProfileListItem(BaseModel):
    id: str
    name: str
    gender: Optional[str]
    age: Optional[int]
    age_group: Optional[str]
    country_id: Optional[str]
    country_name: Optional[str]

    class Config:
        from_attributes = True


class ProfileListResponse(BaseModel):
    status: str
    page: int
    limit: int
    total: int
    data: list[ProfileListItem]
