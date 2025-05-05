from sqlalchemy.orm import Session
from fastapi import Depends, HTTPException, status
from datetime import datetime, timedelta
from typing import Optional, Dict, Any, Tuple
from jose import JWTError

from models.user import User
from models.token import RefreshToken
from models.role import Role
from models.person import Person
from schemas.auth import LoginRequest, RegisterRequest
from schemas.token import Token
from utils.security import (
    verify_password, 
    get_password_hash, 
    create_access_token, 
    create_refresh_token,
    decode_token
)
from database import get_db
from config import settings

class AuthService:
    def __init__(self, db: Session):
        self.db = db
    
    def authenticate_user(self, login_data: LoginRequest) -> Optional[User]:
        """
        Autentica a un usuario con sus credenciales.
        
        Args:
            login_data: Datos de inicio de sesión
            
        Returns:
            Optional[User]: Usuario autenticado o None si no se encuentra
        """
        # Buscar usuario por username o email
        user = self.db.query(User).filter(
            (User.username == login_data.username) | 
            (User.email == login_data.username)
        ).first()
        
        if not user:
            return None
        
        if not user.is_active:
            raise HTTPException(
                status_code=status.HTTP_403_FORBIDDEN,
                detail="Usuario inactivo"
            )
        
        # Verificar contraseña con el nuevo método que incluye salt
        if not verify_password(login_data.password, user.hashed_password, user.salt):
            return None
        
        # Actualizar último inicio de sesión
        user.last_login = datetime.utcnow()
        self.db.commit()
        
        return user
    
    def create_tokens(
        self, 
        user: User, 
        user_agent: Optional[str] = None,
        ip_address: Optional[str] = None,
        remember_me: bool = False
    ) -> Token:
        """
        Crea tokens de acceso y refresco para un usuario.
        
        Args:
            user: Usuario para el que se crean los tokens
            user_agent: Agente de usuario
            ip_address: Dirección IP
            remember_me: Extender la duración del token de refresco
            
        Returns:
            Token: Objeto con los tokens generados
        """
        # Preparar datos para el token
        roles = [role.name for role in user.roles]
        token_data = {
            "sub": str(user.id),
            "username": user.username,
            "roles": roles
        }
        
        # Crear token de acceso
        access_token = create_access_token(token_data)
        
        # Determinar la duración del token de refresco
        if remember_me:
            expires_delta = timedelta(days=settings.REFRESH_TOKEN_EXPIRE_DAYS * 2)
        else:
            expires_delta = settings.refresh_token_expires
        
        # Crear token de refresco
        refresh_token_str = create_refresh_token(token_data, expires_delta)
        
        # Almacenar el refresh token en la base de datos
        refresh_token = RefreshToken(
            token=RefreshToken.generate_token(),
            user_id=user.id,
            expires_at=datetime.utcnow() + expires_delta,
            user_agent=user_agent,
            ip_address=ip_address
        )
        self.db.add(refresh_token)
        self.db.commit()
        
        # Crear respuesta con tokens
        return Token(
            access_token=access_token,
            refresh_token=refresh_token.token,
            token_type="bearer",
            expires_in=settings.ACCESS_TOKEN_EXPIRE_MINUTES * 60  # Convertir a segundos
        )
    
    def register_user(self, user_data: RegisterRequest) -> User:
        """
        Registra un nuevo usuario en el sistema.
        
        Args:
            user_data: Datos para el registro del usuario
            
        Returns:
            User: Usuario creado
            
        Raises:
            HTTPException: Si el nombre de usuario o correo ya existen
        """
        # Verificar si ya existe el username
        if self.db.query(User).filter(User.username == user_data.username).first():
            raise HTTPException(
                status_code=status.HTTP_400_BAD_REQUEST,
                detail="El nombre de usuario ya está en uso"
            )
        
        # Verificar si ya existe el email
        if self.db.query(User).filter(User.email == user_data.email).first():
            raise HTTPException(
                status_code=status.HTTP_400_BAD_REQUEST,
                detail="El correo electrónico ya está registrado"
            )
        
        # Crear la persona asociada al usuario
        person = Person(
            first_name=user_data.first_name,
            last_name=user_data.last_name
        )
        self.db.add(person)
        self.db.flush()  # Para obtener el ID de la persona
        
        # Crear el hash de la contraseña con el método que incluye salt
        hashed_password, salt = get_password_hash(user_data.password)
        
        # Crear el nuevo usuario
        user = User(
            username=user_data.username,
            email=user_data.email,
            hashed_password=hashed_password,
            salt=salt,
            person_id=person.id
        )
        
        # Asignar rol por defecto
        default_role = self.db.query(Role).filter(Role.is_default == True).first()
        if default_role:
            user.roles.append(default_role)
        
        self.db.add(user)
        self.db.commit()
        self.db.refresh(user)
        
        return user
    
    def logout(self, refresh_token: str) -> bool:
        """
        Cierra la sesión de un usuario revocando su token de refresco.
        
        Args:
            refresh_token: Token de refresco a revocar
            
        Returns:
            bool: True si se revocó correctamente
        """
        token = self.db.query(RefreshToken).filter(
            RefreshToken.token == refresh_token,
            RefreshToken.revoked == False
        ).first()
        
        if not token:
            return False
        
        token.revoked = True
        token.revoked_at = datetime.utcnow()
        self.db.commit()
        
        return True
    
    def refresh_access_token(self, refresh_token: str) -> Optional[Token]:
        """
        Refresca el token de acceso usando un token de refresco.
        
        Args:
            refresh_token: Token de refresco
            
        Returns:
            Optional[Token]: Nuevos tokens o None si no es válido
        """
        # Buscar el token en la base de datos
        token_entry = self.db.query(RefreshToken).filter(
            RefreshToken.token == refresh_token,
            RefreshToken.revoked == False,
            RefreshToken.expires_at > datetime.utcnow()
        ).first()
        
        if not token_entry:
            return None
        
        # Obtener el usuario
        user = token_entry.user
        
        if not user or not user.is_active:
            return None
        
        # Crear nuevos tokens
        roles = [role.name for role in user.roles]
        token_data = {
            "sub": str(user.id),
            "username": user.username,
            "roles": roles
        }
        
        access_token = create_access_token(token_data)
        
        # Actualizar la fecha del último uso del token
        token_entry.updated_at = datetime.utcnow()
        self.db.commit()
        
        return Token(
            access_token=access_token,
            refresh_token=token_entry.token,
            token_type="bearer",
            expires_in=settings.ACCESS_TOKEN_EXPIRE_MINUTES * 60  # Convertir a segundos
        )
    
    def verify_token(self, token: str) -> Dict[str, Any]:
        """
        Verifica la validez de un token.
        
        Args:
            token: Token JWT a verificar
            
        Returns:
            Dict[str, Any]: Datos del token si es válido
            
        Raises:
            HTTPException: Si el token no es válido
        """
        try:
            # Decodificar el token
            payload = decode_token(token)
            
            # Verificar si el usuario existe
            user_id = int(payload.get("sub"))
            user = self.db.query(User).filter(User.id == user_id).first()
            
            if not user or not user.is_active:
                raise HTTPException(
                    status_code=status.HTTP_401_UNAUTHORIZED,
                    detail="Usuario no válido o inactivo"
                )
            
            # Verificar tipo de token
            token_type = payload.get("type", "")
            if token_type != "access":
                raise HTTPException(
                    status_code=status.HTTP_401_UNAUTHORIZED,
                    detail="Tipo de token no válido"
                )
            
            return payload
        
        except JWTError:
            raise HTTPException(
                status_code=status.HTTP_401_UNAUTHORIZED,
                detail="Token no válido o expirado"
            )