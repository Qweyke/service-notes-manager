from datetime import datetime
from typing import Dict, Optional

from pydantic import BaseModel


class CreateNoteResponse(BaseModel):
    id: int
    name: str


class CreateNote(BaseModel):
    text: str


class RegisterUserResponse(BaseModel):
    info: str
    name: Optional[str] = None


class RegisterUser(BaseModel):
    name: str
    password: str


class LogIn(BaseModel):
    name: str
    password: str


class LogInResponse(BaseModel):
    name: str
    token: str


class UpdateNoteText(BaseModel):
    text: Optional[str] = None


class UpdateNoteTextResponse(BaseModel):
    id: int
    name: str


class GetNoteTextResponse(BaseModel):
    id: int
    text: str


class GetNoteInfoResponse(BaseModel):
    id: int
    created_at: datetime
    updated_at: datetime


class GetNotesListResponse(BaseModel):
    notes_ids: Dict[int, int]


class DeleteNoteResponse(BaseModel):
    id: int
    name: str


class NoteInfo(BaseModel):
    id: int
    text: str
    created_at: datetime
    updated_at: datetime
    owner: str


from abc import ABC, abstractmethod


class INoteRepository(ABC):
    """
    Interface for permanent note storage
    """

    @abstractmethod
    async def save_note(self, user_name: str, note_id: int, note_data: dict):
        pass

    @abstractmethod
    async def read_note(self, user_name: str, note_id: int) -> Optional[dict]:
        pass

    @abstractmethod
    async def delete_note_file(self, user_name: str, note_id: int):
        pass


class ICacheRepository(ABC):
    """
    Interface for fast metadata and caching
    """

    @abstractmethod
    async def get_string(self, key: str) -> Optional[str]:
        pass

    @abstractmethod
    async def set_string(self, key: str, value: str, ttl: int):
        pass

    @abstractmethod
    async def increment(self, key: str) -> int:
        pass
