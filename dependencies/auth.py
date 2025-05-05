from fastapi import Depends, HTTPException, status, Security
from fastapi.security import OAuth2PasswordBearer, APIKeyHeader
from sqlalchemy.orm import Session
from typing import Dict, Any, Optional, List

from database import get_db
from services.auth import AuthService
from config import settings

# Configuración de OAuth2 para Swagger UI
oauth2_scheme = OAuth2PasswordBearer(tokenUrl="/auth/login/oauth")

# Configuración para autorización mediante header
api_key_header = APIKeyHeader(name="Authorization", auto_error=False)

async def get_token_from_header(
    api_key: Optional[str] = Security(api_key_header)
) -> Optional[str]:
    """
    Extrae el token JWT del header de autorización.
    
    Args:
        api_key: Valor del header Authorization
        
    Returns:
        Optional[str]: Token JWT o None si no existe
    """
    if not api_key:
        return None
    
    parts = api_key.split()
    
    # Verificar formato "Bearer <token>"
    if len(parts) != 2 or parts[0].lower() != "bearer":
        return None
    
    return parts[1]

async def get_current_user(
    token: str = Depends(oauth2_scheme),
    header_token: Optional[str] = Depends(get_token_from_header),
    db: Session = Depends(get_db)
) -> Dict[str, Any]:
    """
    Obtiene el usuario actual a partir del token JWT.
    
    Args:
        token: Token JWT de oauth2_scheme
        header_token: Token JWT del header Authorization
        db: Sesión de base de datos
        
    Returns:
        Dict[str, Any]: Datos del usuario actual
        
    Raises:
        HTTPException: Si el token no es válido
    """
    # Usar el token del header si está disponible, de lo contrario usar el de oauth2_scheme
    jwt_token = header_token or token
    
    if not jwt_token:
        raise HTTPException(
            status_code=status.HTTP_401_UNAUTHORIZED,
            detail="No se proporcionó token de autenticación",
            headers={"WWW-Authenticate": "Bearer"}
        )
    
    auth_service = AuthService(db)
    
    try:
        user_data = auth_service.verify_token(jwt_token)
        return user_data
    except HTTPException as e:
        raise e
    except Exception:
        raise HTTPException(
            status_code=status.HTTP_401_UNAUTHORIZED,
            detail="Token de autenticación inválido",
            headers={"WWW-Authenticate": "Bearer"}
        )

def has_role(required_roles: List[str]):
    """
    Dependencia para verificar si el usuario tiene alguno de los roles requeridos.
    
    Args:
        required_roles: Lista de roles requeridos
        
    Returns:
        Callable: Función de dependencia
    """
    async def _has_role(
        current_user: Dict[str, Any] = Security(get_current_user)
    ) -> Dict[str, Any]:
        user_roles = current_user.get("roles", [])
        
        # Verificar si alguno de los roles del usuario está en los roles requeridos
        if not any(role in required_roles for role in user_roles):
            raise HTTPException(
                status_code=status.HTTP_403_FORBIDDEN,
                detail="No tienes permiso para acceder a este recurso"
            )
        
        return current_user
    
    return _has_role

def is_admin(
    current_user: Dict[str, Any] = Security(get_current_user)
) -> Dict[str, Any]:
    """
    Verifica si el usuario tiene rol de administrador.
    
    Args:
        current_user: Datos del usuario actual
        
    Returns:
        Dict[str, Any]: Datos del usuario si es administrador
        
    Raises:
        HTTPException: Si el usuario no es administrador
    """
    user_roles = current_user.get("roles", [])
    
    if "admin" not in user_roles:
        raise HTTPException(
            status_code=status.HTTP_403_FORBIDDEN,
            detail="Se requiere rol de administrador"
        )
    
    return current_user