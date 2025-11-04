from sqlalchemy import create_engine
from sqlalchemy.ext.declarative import declarative_base
from sqlalchemy.orm import sessionmaker
from dotenv import load_dotenv
import os

# .env 파일 로드
load_dotenv()

# .env 파일 내 DATABASE_URL 예시:
# DATABASE_URL=postgresql+psycopg2://username:password@localhost:5432/dbname

DATABASE_URL = os.getenv("DATABASE_URL")

print(f"✅ DATABASE_URL loaded: {DATABASE_URL}")  # 확인용

if not DATABASE_URL:
    raise ValueError("❌ DATABASE_URL is missing from .env file!")

# SQLAlchemy 엔진 생성
# echo=True → 쿼리 로그 출력 (개발 단계에서는 켜두면 유용)
engine = create_engine(DATABASE_URL, echo=True)

# 세션 로컬 설정
SessionLocal = sessionmaker(autocommit=False, autoflush=False, bind=engine)

# Base 클래스 (모든 ORM 모델이 상속받음)
Base = declarative_base()

# 서버 실행 시 테이블 자동 생성 (임시)
Base.metadata.create_all(bind=engine)

# ✅ 의존성 주입용 DB 세션 함수
# - FastAPI의 Depends에서 사용됨
def get_db():
    db = SessionLocal()
    try:
        yield db
    finally:
        db.close()
