import io

from fastapi import FastAPI, Depends, HTTPException, File
from fastapi.responses import Response
from pydub import AudioSegment
from pydub.exceptions import CouldntDecodeError
from sqlalchemy.orm import Session

from config import DB_HOST, DB_PORT
from src.database import SessionLocal
from src.models import User, Audio

# приложение
app = FastAPI()


# определяем зависимость
def get_db():
    db = SessionLocal()
    try:
        yield db
    finally:
        db.close()


@app.post("/")
def create_user(name: str, db: Session = Depends(get_db)):
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


def get_user_media(id: int, token: str, db: Session = Depends(get_db)):
    user = db.query(User).filter(User.token == token, User.id == id).first()
    return user


def to_wav_from_mp3(audio_file: bytes):
    wav_media = AudioSegment.from_wav(io.BytesIO(audio_file))

    mp3_media = io.BytesIO()
    wav_media.export(mp3_media, format='mp3')
    mp3_media.seek(0)
    mp3_read = mp3_media.read()

    return mp3_read


@app.post("/r")
def load_media(id: int, token: str, audio_file: bytes = File(), db: Session = Depends(get_db)):
    user = get_user_media(id, token, db)
    if user is None:
        raise HTTPException(
            status_code=404,
            detail='Пользователь не найден'
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
            detail=f'Wrong file format: {e}'
        )


@app.get('/record')
def download_media(id: int, user: str, db: Session = Depends(get_db)):
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
