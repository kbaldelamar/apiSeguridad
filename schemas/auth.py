from pydantic import BaseModel, Field, validator
from typing import Optional

class LoginRequest(BaseModel):
    username: str = Field(..., description="Nombre de usuario o correo electrónico")
    password: str = Field(..., description="Contraseña del usuario")
    remember_me: Optional[bool] = Field(False, description="Mantener la sesión activa")

class LoginResponse(BaseModel):
    access_token: str
    refresh_token: str
    token_type: str = "bearer"
    expires_in: int  # En segundos
    user_id: int
    username: str

class RegisterRequest(BaseModel):
    username: str = Field(..., min_length=3, max_length=50)
    email: str = Field(..., pattern=r"^[a-zA-Z0-9_.+-]+@[a-zA-Z0-9-]+\.[a-zA-Z0-9-.]+$")
    password: str = Field(..., min_length=8)
    confirm_password: str = Field(...)
    first_name: str = Field(..., min_length=2, max_length=50)
    last_name: str = Field(..., min_length=2, max_length=50)
    
    @validator("confirm_password")
    def passwords_match(cls, v, values):
        if "password" in values and v != values["password"]:
            raise ValueError("Las contraseñas no coinciden")
        return v

class VerifyEmailRequest(BaseModel):
    email: str
    verification_code: str

class VerificationResponse(BaseModel):
    message: str
    success: bool

class LogoutRequest(BaseModel):
    refresh_token: str