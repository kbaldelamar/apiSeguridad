from sqlalchemy import Column, Integer, String, Date, ForeignKey, Boolean, DateTime, Enum
from sqlalchemy.orm import relationship
from sqlalchemy.sql import func
import enum

from database import Base

class GenderEnum(enum.Enum):
    MALE = "male"
    FEMALE = "female"
    OTHER = "other"
    NOT_SPECIFIED = "not_specified"

class Person(Base):
    __tablename__ = "persons"

    id = Column(Integer, primary_key=True, index=True)
    first_name = Column(String(50), nullable=False)
    last_name = Column(String(50), nullable=False)
    document_type = Column(String(20), nullable=True)
    document_number = Column(String(20), nullable=True, index=True)
    birth_date = Column(Date, nullable=True)
    gender = Column(Enum(GenderEnum), default=GenderEnum.NOT_SPECIFIED)
    address = Column(String(200), nullable=True)
    city = Column(String(50), nullable=True)
    state = Column(String(50), nullable=True)
    country = Column(String(50), nullable=True)
    postal_code = Column(String(20), nullable=True)
    phone_number = Column(String(20), nullable=True)
    mobile_number = Column(String(20), nullable=True)
    emergency_contact = Column(String(100), nullable=True)
    emergency_phone = Column(String(20), nullable=True)
    created_at = Column(DateTime, server_default=func.now())
    updated_at = Column(DateTime, server_default=func.now(), onupdate=func.now())
    
    # Relación uno a uno con Usuario
    user = relationship("User", back_populates="person", uselist=False)
    
    def __repr__(self):
        return f"Person(id={self.id}, name={self.first_name} {self.last_name})"
    
    @property
    def full_name(self):
        return f"{self.first_name} {self.last_name}"