from sqlalchemy import Column, Integer, String, DateTime
from database import Base

class Subscription(Base):
    __tablename__ = 'subscriptions'
    
    id = Column(Integer, primary_key=True)
    user_id = Column(Integer)
    start_date = Column(DateTime)
    end_date = Column(DateTime)
    payment_method = Column(String)