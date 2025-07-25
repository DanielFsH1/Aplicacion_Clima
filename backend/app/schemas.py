from datetime import datetime
from typing import Optional
from pydantic import BaseModel

class LocationBase(BaseModel):
    name: str
    lat: float
    lon: float
    country: Optional[str] = None
    state: Optional[str] = None

class LocationCreate(LocationBase):
    pass

class Location(LocationBase):
    id: int

    class Config:
        orm_mode = True

class Favorite(BaseModel):
    id: int
    location: Location
    created_at: datetime

    class Config:
        orm_mode = True
