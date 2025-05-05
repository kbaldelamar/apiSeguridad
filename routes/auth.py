from fastapi import APIRouter, Depends, HTTPException, status, Request
from fastapi.security import OAuth2PasswordRequestForm
from sqlalchemy.orm import Session
from typing_extensions import Annotated

from database import get_db
from services.auth import AuthService
from schemas.auth import (
    LoginRequest, 
    LoginResponse, 
    RegisterRequest, 
    VerifyEmailRequest, 
    VerificationResponse,
    LogoutRequest
)
from schemas.user import UserResponse
from schemas.token import Token, RefreshTokenRequest
from models.person import Person

router = APIRouter(prefix="/auth", tags=["auth"])

@router.post("/login", response_model=LoginResponse)
async def login(
    login_data: LoginRequest,
    request: Request,
    db: Session = Depends(get_db)
):
    """
    Endpoint para iniciar sesión y obtener tokens de autenticación.
    """
    auth_service = AuthService(db)
    
    user = auth_service.authenticate_user(login_data)
    if not user:
        raise HTTPException(
            status_code=status.HTTP_401_UNAUTHORIZED,
            detail="Credenciales incorrectas"
        )
    
    # Obtener información del cliente
    user_agent = request.headers.get("user-agent", "")
    client_host = request.client.host if request.client else None
    
    # Crear tokens
    tokens = auth_service.create_tokens(
        user, 
        user_agent=user_agent,
        ip_address=client_host,
        remember_me=login_data.remember_me
    )
    
    return LoginResponse(
        access_token=tokens.access_token,
        refresh_token=tokens.refresh_token,
        token_type=tokens.token_type,
        expires_in=tokens.expires_in,
        user_id=user.id,
        username=user.username
    )

@router.post("/login/oauth", response_model=LoginResponse)
async def login_oauth(
    request: Request,
    form_data: OAuth2PasswordRequestForm = Depends(),
    db: Session = Depends(get_db)
):
    """
    Endpoint para iniciar sesión usando OAuth2 Password Grant.
    """
    login_data = LoginRequest(
        username=form_data.username,
        password=form_data.password
    )
    
    return await login(login_data, request, db)

@router.post("/register", response_model=UserResponse, status_code=status.HTTP_201_CREATED)
async def register(
    user_data: RegisterRequest,
    db: Session = Depends(get_db)
):
    """
    Registra un nuevo usuario en el sistema.
    """
    auth_service = AuthService(db)
    
    # Comprobar que las contraseñas coinciden
    if user_data.password != user_data.confirm_password:
        raise HTTPException(
            status_code=status.HTTP_400_BAD_REQUEST,
            detail="Las contraseñas no coinciden"
        )
    
    # Crear el usuario
    user = auth_service.register_user(user_data)
    
    # Convertir roles a lista de strings para la respuesta
    roles = [role.name for role in user.roles]
    
    # Obtener la persona relacionada
    person = db.query(Person).filter(Person.id == user.person_id).first()
    first_name = person.first_name if person else None
    last_name = person.last_name if person else None
    
    return UserResponse(
        id=user.id,
        username=user.username,
        email=user.email,
        is_active=user.is_active,
        is_verified=user.is_verified,
        created_at=user.created_at,
        updated_at=user.updated_at,
        roles=roles,
        first_name=first_name,
        last_name=last_name
    )

@router.post("/verify-email", response_model=VerificationResponse)
async def verify_email(
    verification_data: VerifyEmailRequest,
    db: Session = Depends(get_db)
):
    """
    Verifica el correo electrónico de un usuario.
    """
    from models.user import User
    
    user = db.query(User).filter(
        User.email == verification_data.email,
        User.verification_code == verification_data.verification_code,
        User.is_verified == False
    ).first()
    
    if not user:
        raise HTTPException(
            status_code=status.HTTP_400_BAD_REQUEST,
            detail="Código de verificación inválido o ya utilizado"
        )
    
    user.is_verified = True
    user.verification_code = None
    db.commit()
    
    return VerificationResponse(
        message="Correo electrónico verificado correctamente",
        success=True
    )

@router.post("/refresh-token", response_model=Token)
async def refresh_token(
    refresh_data: RefreshTokenRequest,
    db: Session = Depends(get_db)
):
    """
    Refresca el token de acceso utilizando un token de refresco.
    """
    auth_service = AuthService(db)
    
    tokens = auth_service.refresh_access_token(refresh_data.refresh_token)
    if not tokens:
        raise HTTPException(
            status_code=status.HTTP_401_UNAUTHORIZED,
            detail="Token de refresco inválido o expirado"
        )
    
    return tokens

@router.post("/logout", status_code=status.HTTP_204_NO_CONTENT)
async def logout(
    logout_data: LogoutRequest,
    db: Session = Depends(get_db)
):
    """
    Cierra la sesión revocando el token de refresco.
    """
    auth_service = AuthService(db)
    
    success = auth_service.logout(logout_data.refresh_token)
    if not success:
        raise HTTPException(
            status_code=status.HTTP_400_BAD_REQUEST,
            detail="Token de refresco inválido"
        )
    
    return None