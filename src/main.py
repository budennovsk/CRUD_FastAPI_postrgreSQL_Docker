from fastapi import FastAPI, Depends
from sqlalchemy.orm import Session
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
def create_person(name: str, db: Session = Depends(get_db)):
    person = User(name=name)
    db.add(person)
    db.commit()
    db.refresh(person)


@app.get("/")
def create_person(db: Session = Depends(get_db)):
    return {'ff': db.query(User).all()}
