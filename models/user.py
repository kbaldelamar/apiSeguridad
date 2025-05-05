from sqlalchemy import Column, Integer, String, Boolean, ForeignKey, DateTime, Table
from sqlalchemy.orm import relationship
from sqlalchemy.sql import func
import uuid

from database import Base

# Tabla de asociación para la relación muchos-a-muchos entre usuarios y roles
user_roles = Table('user_roles', Base.metadata,
    Column('user_id', Integer, ForeignKey('users.id')),
    Column('role_id', Integer, ForeignKey('roles.id'))
)

class User(Base):
    __tablename__ = "users"

    id = Column(Integer, primary_key=True, index=True)
    username = Column(String(50), unique=True, index=True, nullable=False)
    email = Column(String(100), unique=True, index=True, nullable=False)
    hashed_password = Column(String(255), nullable=False)
    salt = Column(String(100), nullable=False)  # Campo para almacenar el salt único del usuario
    is_active = Column(Boolean, default=True)
    is_verified = Column(Boolean, default=False)
    verification_code = Column(String(36), default=lambda: str(uuid.uuid4()), nullable=True)
    reset_password_token = Column(String(36), nullable=True)
    reset_password_expires = Column(DateTime, nullable=True)
    last_login = Column(DateTime, nullable=True)
    created_at = Column(DateTime, server_default=func.now())
    updated_at = Column(DateTime, server_default=func.now(), onupdate=func.now())
    person_id = Column(Integer, ForeignKey("persons.id"), nullable=True)  # Referencia a la persona

    # Relaciones
    roles = relationship("Role", secondary=user_roles, back_populates="users")
    refresh_tokens = relationship("RefreshToken", back_populates="user", cascade="all, delete-orphan")
    person = relationship("Person", back_populates="user")  # Relación con Persona
    
    def __repr__(self):
        return f"User(id={self.id}, username={self.username}, email={self.email})"