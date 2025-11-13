# app/schemas/chat.py
from typing import List, Optional
from datetime import datetime
from pydantic import BaseModel
from fastapi import UploadFile, Form


# -----------------------------
# 공통 / 멤버 스키마
# -----------------------------
class ChatMemberResponse(BaseModel):
    user_id: int
    username: str
    account_id: Optional[str] = None
    profile_image_url: Optional[str] = None

    class Config:
        orm_mode = True


# -----------------------------
# 요청 스키마
# -----------------------------
class ChatRoomCreateRequest(BaseModel):
    """
    POST /api/chats
    새 채팅방 생성 요청
    """
    other_user_id: int  # 1:1 채팅 상대


class MessageCreateRequest(BaseModel):
    """
    POST / WebSocket "send_message"
    새 메시지 생성 요청
    """
    content: Optional[str] = None
    image: Optional[UploadFile] = None
    
    @classmethod
    def as_form(
        cls,
        content: Optional[str] = Form(None),
        image: Optional[UploadFile] = None
    ):
        return cls(content=content, image=image)

class MessageUpdateRequest(BaseModel):
    """
    PATCH /api/chats/{chat_id}/messages/{message_id}
    메시지 수정
    """
    content: Optional[str] = None
    image: Optional[str] = None


# -----------------------------
# 메시지 응답 스키마
# -----------------------------
class MessageResponse(BaseModel):
    id: int
    chatroom_id: int
    sender_id: int
    sender_username: str
    sender_account_id: Optional[str] = None
    sender_profile_image_url: Optional[str] = None
    content: Optional[str] = None
    image_url: Optional[str] = None
    created_at: datetime
    is_deleted: bool
    is_blurred: bool
    report_count: int
    read_user_ids: List[int] = []  # 메시지 읽은 사용자 ID 목록

    class Config:
        orm_mode = True


# -----------------------------
# 채팅방 응답 스키마
# -----------------------------
class ChatRoomResponse(BaseModel):
    id: int
    members: List[ChatMemberResponse]
    last_message: Optional[MessageResponse] = None
    unread_count: int
    last_message_at: datetime

    class Config:
        orm_mode = True


# -----------------------------
# WebSocket 이벤트용 스키마
# -----------------------------
class WSMessageSend(BaseModel):
    chatroom_id: int
    content: Optional[str] = None
    image_url: Optional[str] = None


class WSMessageReceive(MessageResponse):
    """
    서버 → 클라이언트로 브로드캐스트되는 메시지
    """
    pass


class WSMessageReadUpdate(BaseModel):
    message_id: int
    user_id: int

    class Config:
        orm_mode = True
