from sqlalchemy import Column, Integer, String, ForeignKey, DateTime, Boolean
from sqlalchemy.orm import relationship
from sqlalchemy.sql import func
import uuid

from database import Base

class RefreshToken(Base):
    __tablename__ = "refresh_tokens"

    id = Column(Integer, primary_key=True, index=True)
    token = Column(String(255), unique=True, nullable=False, index=True)
    user_id = Column(Integer, ForeignKey("users.id"), nullable=False)
    expires_at = Column(DateTime, nullable=False)
    revoked = Column(Boolean, default=False)
    revoked_at = Column(DateTime, nullable=True)
    created_at = Column(DateTime, server_default=func.now())
    updated_at = Column(DateTime, server_default=func.now(), onupdate=func.now())
    user_agent = Column(String(255), nullable=True)
    ip_address = Column(String(45), nullable=True)  # IPv6 addresses pueden ser largas

    # Relaciones
    user = relationship("User", back_populates="refresh_tokens")
    
    @classmethod
    def generate_token(cls):
        """Genera un token único para refresh token"""
        return str(uuid.uuid4())
    
    def __repr__(self):
        return f"RefreshToken(id={self.id}, user_id={self.user_id}, expires_at={self.expires_at})"