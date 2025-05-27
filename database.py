from sqlalchemy import create_engine
from sqlalchemy.ext.declarative import declarative_base
from sqlalchemy.orm import sessionmaker, scoped_session
from config import Config

engine = create_engine(
    Config.DB_URL,
    pool_size=20,
    max_overflow=10,
    pool_pre_ping=True
)

Base = declarative_base()
Session = scoped_session(sessionmaker(bind=engine))

def get_db():
    db = Session()
    try:
        yield db
    finally:
        db.close()