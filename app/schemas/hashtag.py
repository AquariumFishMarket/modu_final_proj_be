# schemas/hashtag.py
from pydantic import BaseModel
from typing import Optional


# --- 공통 스키마 ---
class HashtagBase(BaseModel):
    name: str


# --- 요청 스키마 ---
class HashtagCreate(HashtagBase):
    pass


class HashtagUpdate(BaseModel):
    name: Optional[str] = None


# --- 응답 스키마 ---
class HashtagResponse(BaseModel):
    id: int
    name: str

    class Config:
        orm_mode = True
