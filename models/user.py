from sqlalchemy import Column, Integer, String, Boolean
from database import Base

class User(Base):
    __tablename__ = 'users'
    
    id = Column(Integer, primary_key=True)
    user_id = Column(Integer, unique=True, nullable=False)
    username = Column(String(64), index=True)
    is_admin = Column(Boolean, default=False, nullable=False)
    language = Column(String(8), default='fa', nullable=False)