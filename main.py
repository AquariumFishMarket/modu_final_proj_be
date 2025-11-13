from fastapi import FastAPI, Depends
from sqlalchemy.orm import Session
from sqlalchemy import text
from app.database import Base, engine, get_db
from app.routers import auth, user

app = FastAPI()

# ORM 모델 import (예시로 user.py가 있다면)
# from app.models import user

app.include_router(auth.router)
app.include_router(user.router)

@app.get("/")
def root():
    return {"message": "🚀 FastAPI is running and connected to PostgreSQL!"}


# DB 연결 테스트용 엔드포인트
@app.get("/test-db")
def test_db_connection(db: Session = Depends(get_db)):
    try:
        db.execute(text("SELECT 1"))  # 단순한 쿼리 실행
        return {"status": "success", "detail": "Database connection works!"}
    except Exception as e:
        return {"status": "error", "detail": str(e)}
