import io

from fastapi import FastAPI, Depends, HTTPException, UploadFile, status
from fastapi.responses import Response
from pydub import AudioSegment
from pydub.exceptions import CouldntDecodeError
from sqlalchemy.orm import Session

from config import DB_HOST, DB_PORT
from src.database import SessionLocal
from src.models import User, Audio

from src.schemas import *

# приложение
app = FastAPI()


# определяем зависимость
def get_db():
    db = SessionLocal()
    try:
        yield db
    finally:
        db.close()


@app.post("/create", response_model=CreateUser, status_code=status.HTTP_201_CREATED)
def create_user(name: str, db: Session = Depends(get_db)):
    """ Функция создания пользователя в БД"""
    if db.query(User).filter(User.name == name).first():
        raise HTTPException(
            status_code=409,
            detail='Пользователь уже существует'
        )
    user = User(name=name)
    db.add(user)
    db.commit()
    db.refresh(user)
    return user


def get_user_media(id: int, token: str, db: Session = Depends(get_db)) -> object:
    """Получение пользователя"""
    user = db.query(User).filter(User.token == token, User.id == id).first()
    return user


def to_wav_from_mp3(audio_file) -> bytes:
    """Конвертация аудио в БД"""
    wav_media = AudioSegment.from_wav(audio_file.file)
    mp3_media = io.BytesIO()
    wav_media.export(mp3_media, format='mp3')
    mp3_media.seek(0)
    mp3_read = mp3_media.read()
    return mp3_read


@app.post("/upload", response_model=UploadMusic, status_code=status.HTTP_201_CREATED)
def load_media(id: int, token: str, audio_file: UploadFile, db: Session = Depends(get_db)):
    """Конвертация WAVE в mp3 и добавление в БД """
    user = get_user_media(id, token, db)
    expansion = audio_file.filename.split('.')[2]
    if user is None:
        raise HTTPException(
            status_code=404,
            detail='Пользователь не найден'
        )

    if not expansion:
        raise HTTPException(
            status_code=400,
            detail=f'Неверное расширение файла {expansion}, необходимо WAV'
        )
    if audio_file.size > 5000000:
        raise HTTPException(
            status_code=400,
            detail=f'Превышен размер допустимого файла {audio_file.size}, максимум 5 МБ'
        )
    try:
        mp3_audio = to_wav_from_mp3(audio_file)
        audio = Audio(
            user_id=user.id,
            audio=mp3_audio
        )
        db.add(audio)
        db.commit()
        db.refresh(audio)
        url = f'http://{DB_HOST}:{DB_PORT}/record?id={audio.id}&user={audio.user_id}'
        return {'url': url}

    except CouldntDecodeError as e:
        raise HTTPException(
            status_code=422,
            detail=f'Ошибка с описание: {e}'
        )


@app.get('/record', response_model=str, status_code=status.HTTP_200_OK)
def download_media(id: int, user: str, db: Session = Depends(get_db)):
    """Скачивание mp3 из БД"""
    search_mp3 = db.query(Audio).filter(Audio.id == user, Audio.user_id == id).first()

    if search_mp3 is None:
        raise HTTPException(
            status_code=404,
            detail='Файл не найден'
        )
    save_mp3 = io.BytesIO(search_mp3.audio).read()

    return Response(
        content=save_mp3,
        media_type='audio/mpeg',
        headers={
            'Content-Disposition': f'attachment; filename="{search_mp3.id}"'
        }
    )
