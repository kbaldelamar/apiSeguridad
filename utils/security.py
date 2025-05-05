from passlib.context import CryptContext
from jose import jwt, JWTError
from datetime import datetime, timedelta
import uuid
import os
import hashlib
import base64
from typing import Dict, Any, Optional, List, Union, Tuple

from config import settings

# Configuración del contexto para hashing de contraseñas
pwd_context = CryptContext(schemes=["bcrypt"], deprecated="auto")

def generate_salt() -> str:
    """
    Genera un salt aleatorio para el hashing de contraseñas.
    
    Returns:
        str: Salt aleatorio en formato base64
    """
    return base64.b64encode(os.urandom(32)).decode('utf-8')

def get_password_hash(password: str, salt: Optional[str] = None) -> Tuple[str, str]:
    """
    Genera un hash para la contraseña proporcionada con un salt único.
    
    Args:
        password: Contraseña en texto plano
        salt: Salt opcional (se genera uno nuevo si no se proporciona)
        
    Returns:
        Tuple[str, str]: (Hash de la contraseña, salt utilizado)
    """
    if not salt:
        salt = generate_salt()
    
    # Primera capa: Hash con salt personalizado
    salted_password = (password + salt).encode('utf-8')
    hash_pass = hashlib.sha256(salted_password).hexdigest()
    
    # Segunda capa: Hash bcrypt (incluye su propio salt interno)
    hashed_password = pwd_context.hash(hash_pass)
    
    return hashed_password, salt

def verify_password(plain_password: str, hashed_password: str, salt: str) -> bool:
    """
    Verifica si la contraseña en texto plano coincide con el hash.
    
    Args:
        plain_password: Contraseña en texto plano
        hashed_password: Hash de la contraseña almacenada
        salt: Salt utilizado para el hash
        
    Returns:
        bool: True si coinciden, False en caso contrario
    """
    # Aplicar el mismo proceso que al crear el hash
    salted_password = (plain_password + salt).encode('utf-8')
    hash_pass = hashlib.sha256(salted_password).hexdigest()
    
    # Verificar contra el hash bcrypt
    return pwd_context.verify(hash_pass, hashed_password)

def create_access_token(
    data: Dict[str, Any], 
    expires_delta: Optional[timedelta] = None
) -> str:
    """
    Crea un token JWT de acceso.
    
    Args:
        data: Datos a incluir en el token
        expires_delta: Tiempo de expiración
        
    Returns:
        str: Token JWT
    """
    to_encode = data.copy()
    if expires_delta:
        expire = datetime.utcnow() + expires_delta
    else:
        expire = datetime.utcnow() + settings.access_token_expires
    
    jti = str(uuid.uuid4())  # JWT ID único
    iat = datetime.utcnow()  # Issued At
    
    to_encode.update({
        "exp": expire,
        "iat": iat,
        "jti": jti,
        "type": "access"
    })
    
    encoded_jwt = jwt.encode(
        to_encode, 
        settings.SECRET_KEY, 
        algorithm=settings.ACCESS_TOKEN_ALGORITHM
    )
    return encoded_jwt

def create_refresh_token(
    data: Dict[str, Any], 
    expires_delta: Optional[timedelta] = None
) -> str:
    """
    Crea un token JWT de refresco.
    
    Args:
        data: Datos a incluir en el token
        expires_delta: Tiempo de expiración
        
    Returns:
        str: Token JWT
    """
    to_encode = data.copy()
    if expires_delta:
        expire = datetime.utcnow() + expires_delta
    else:
        expire = datetime.utcnow() + settings.refresh_token_expires
    
    jti = str(uuid.uuid4())  # JWT ID único
    iat = datetime.utcnow()  # Issued At
    
    to_encode.update({
        "exp": expire,
        "iat": iat,
        "jti": jti,
        "type": "refresh"
    })
    
    encoded_jwt = jwt.encode(
        to_encode, 
        settings.SECRET_KEY, 
        algorithm=settings.ACCESS_TOKEN_ALGORITHM
    )
    return encoded_jwt

def decode_token(token: str) -> Dict[str, Any]:
    """
    Decodifica un token JWT.
    
    Args:
        token: Token JWT a decodificar
        
    Returns:
        Dict[str, Any]: Datos del token decodificado
        
    Raises:
        JWTError: Si el token no es válido
    """
    return jwt.decode(
        token, 
        settings.SECRET_KEY, 
        algorithms=[settings.ACCESS_TOKEN_ALGORITHM]
    )

def create_verification_code() -> str:
    """
    Genera un código de verificación único.
    
    Returns:
        str: Código de verificación
    """
    return str(uuid.uuid4())

def generate_random_password(length: int = 12) -> str:
    """
    Genera una contraseña aleatoria segura.
    
    Args:
        length: Longitud de la contraseña
        
    Returns:
        str: Contraseña aleatoria
    """
    import secrets
    import string
    
    alphabet = string.ascii_letters + string.digits + string.punctuation
    return ''.join(secrets.choice(alphabet) for _ in range(length))