import uuid

from pydantic import BaseModel


class CreateUser(BaseModel):
    token: uuid.UUID
    name: str
    id: int

    class Config:
        orm_mode = True


class UploadMusic(BaseModel):
    url = dict
