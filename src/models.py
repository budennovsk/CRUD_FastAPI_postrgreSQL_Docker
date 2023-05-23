import uuid
from sqlalchemy.dialects.postgresql import UUID
from sqlalchemy import Column, Integer, ForeignKey, LargeBinary, String
from sqlalchemy.orm import relationship

from src.database import Base, engine


# создаем модель, объекты которой будут храниться в бд
class User(Base):
    __tablename__ = "user"

    id = Column(Integer, primary_key=True, index=True)
    name = Column(String, nullable=False, unique=True)
    token = Column(UUID(as_uuid=True), default=uuid.uuid4)


# создаем модель, объекты которой будут храниться в бд
class Audio(Base):
    __tablename__ = "audio"

    id = Column(UUID(as_uuid=True), primary_key=True, default=uuid.uuid4)
    user_id = Column(Integer, ForeignKey("user.id"))
    audio = Column(LargeBinary, nullable=False)
    user = relationship("User", backref="audio")


# создаем таблицы
Base.metadata.create_all(bind=engine)
