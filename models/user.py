from sqlalchemy import Column, Integer, BigInteger, String, Boolean, DateTime, func, Text
from db.base import Base

class User(Base):
    __tablename__ = 'users'
    
    id = Column(Integer, primary_key=True)
    telegram_id = Column(BigInteger, nullable=False)
    telegram_name = Column(String(255), nullable=True)
    ozon_seller_token = Column(String(255), nullable=True)
    is_ozon_seller_token_valid = Column(Boolean, nullable=False, default=False)
    ozon_performance_token = Column(String(255), nullable=True)
    is_performance_token_valid = Column(Boolean, nullable=False, default=False)
    current_state = Column(String(50), nullable=True)
    created_at = Column(DateTime, nullable=False, server_default=func.now())
    updated_at = Column(DateTime, nullable=False, server_default=func.now(), onupdate=func.now())
    deleted = Column(Boolean, nullable=False, default=False)
    last_message_id = Column(BigInteger, nullable=True)
    ozon_seller_client_id = Column(String(255), nullable=True)
    ozon_performance_client_id = Column(String(255), nullable=True)
    ozon_performance_session_token = Column(Text(), nullable=True)
    
    def __repr__(self):
        return f"<User(id={self.id}, telegram_id={self.telegram_id})>"