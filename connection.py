from config import DB_NAME, DB_HOST, DB_PORT, DB_USER, DB_PASS
from sqlalchemy import create_engine
from model import Base
from sqlalchemy.orm import sessionmaker

db_url = f'postgresql://{DB_USER}:{DB_PASS}@{DB_HOST}:{DB_PORT}/{DB_NAME}'
engine = create_engine(db_url)

Base.metadata.create_all(engine)

SessionLocal = sessionmaker(autocommit=False, autoflush=False, bind=engine)

def get_db():
    db = SessionLocal()
    try:
        yield db
    finally:
        db.close()