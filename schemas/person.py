from pydantic import BaseModel, Field, validator
from typing import Optional
from datetime import date
from enum import Enum

class GenderEnum(str, Enum):
    MALE = "male"
    FEMALE = "female"
    OTHER = "other"
    NOT_SPECIFIED = "not_specified"

class PersonBase(BaseModel):
    first_name: str = Field(..., min_length=2, max_length=50)
    last_name: str = Field(..., min_length=2, max_length=50)
    
    model_config = {"from_attributes": True}

class PersonCreate(PersonBase):
    document_type: Optional[str] = Field(None, max_length=20)
    document_number: Optional[str] = Field(None, max_length=20)
    birth_date: Optional[date] = None
    gender: Optional[GenderEnum] = GenderEnum.NOT_SPECIFIED
    address: Optional[str] = Field(None, max_length=200)
    city: Optional[str] = Field(None, max_length=50)
    state: Optional[str] = Field(None, max_length=50)
    country: Optional[str] = Field(None, max_length=50)
    postal_code: Optional[str] = Field(None, max_length=20)
    phone_number: Optional[str] = Field(None, max_length=20)
    mobile_number: Optional[str] = Field(None, max_length=20)
    emergency_contact: Optional[str] = Field(None, max_length=100)
    emergency_phone: Optional[str] = Field(None, max_length=20)

class PersonUpdate(BaseModel):
    first_name: Optional[str] = Field(None, min_length=2, max_length=50)
    last_name: Optional[str] = Field(None, min_length=2, max_length=50)
    document_type: Optional[str] = Field(None, max_length=20)
    document_number: Optional[str] = Field(None, max_length=20)
    birth_date: Optional[date] = None
    gender: Optional[GenderEnum] = None
    address: Optional[str] = Field(None, max_length=200)
    city: Optional[str] = Field(None, max_length=50)
    state: Optional[str] = Field(None, max_length=50)
    country: Optional[str] = Field(None, max_length=50)
    postal_code: Optional[str] = Field(None, max_length=20)
    phone_number: Optional[str] = Field(None, max_length=20)
    mobile_number: Optional[str] = Field(None, max_length=20)
    emergency_contact: Optional[str] = Field(None, max_length=100)
    emergency_phone: Optional[str] = Field(None, max_length=20)
    
    model_config = {"from_attributes": True}

class PersonResponse(PersonBase):
    id: int
    document_type: Optional[str] = None
    document_number: Optional[str] = None
    birth_date: Optional[date] = None
    gender: Optional[GenderEnum] = GenderEnum.NOT_SPECIFIED
    address: Optional[str] = None
    city: Optional[str] = None
    state: Optional[str] = None
    country: Optional[str] = None
    postal_code: Optional[str] = None
    phone_number: Optional[str] = None
    mobile_number: Optional[str] = None
    
    model_config = {"from_attributes": True}
    
    @property
    def full_name(self) -> str:
        return f"{self.first_name} {self.last_name}"