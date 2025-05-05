from pydantic import BaseModel
from typing import Optional, List
from datetime import datetime

class Token(BaseModel):
    access_token: str
    refresh_token: str
    token_type: str = "bearer"
    expires_in: int  # en segundos

class TokenData(BaseModel):
    sub: str  # Sujeto (generalmente user_id)
    exp: datetime  # Tiempo de expiración
    iat: datetime  # Tiempo de emisión
    jti: str  # ID único del token
    type: str  # Tipo de token (access, refresh)
    username: Optional[str] = None
    roles: List[str] = []
    permissions: List[str] = []

class RefreshTokenRequest(BaseModel):
    refresh_token: str

class RevokeTokenRequest(BaseModel):
    token: str
    token_type_hint: Optional[str] = "refresh_token"  # Puede ser "access_token" o "refresh_token"

class TokenVerifyResponse(BaseModel):
    is_valid: bool
    user_id: Optional[int] = None
    username: Optional[str] = None
    roles: List[str] = []
    permissions: List[str] = []
    expires_at: Optional[datetime] = None
    
    model_config = {"from_attributes": True}

class TokenIntrospection(BaseModel):
    active: bool
    client_id: Optional[str] = None
    username: Optional[str] = None
    scope: Optional[str] = None
    token_type: Optional[str] = None
    exp: Optional[int] = None
    iat: Optional[int] = None
    nbf: Optional[int] = None
    sub: Optional[str] = None
    aud: Optional[List[str]] = None
    iss: Optional[str] = None
    jti: Optional[str] = None