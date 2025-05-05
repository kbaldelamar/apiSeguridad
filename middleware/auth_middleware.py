from fastapi import Request, HTTPException, status
from fastapi.responses import JSONResponse
from jose import JWTError
from sqlalchemy.orm import Session
from typing import Callable, Dict, Any, Optional, List

from utils.security import decode_token
from database import SessionLocal
from config import settings
from starlette.types import ASGIApp, Scope, Receive, Send

class AuthMiddleware:
    """
    Middleware para verificar la autenticación en rutas protegidas.
    """
    
    def __init__(
        self,
        app: ASGIApp,  # Este es el primer parámetro que FastAPI pasa automáticamente
        public_paths: List[str] = None,
        exclude_paths: List[str] = None
    ):
        """
        Inicializa el middleware de autenticación.
        
        Args:
            app: Aplicación ASGI
            public_paths: Lista de rutas públicas que no requieren autenticación
            exclude_paths: Lista de rutas que no serán procesadas por el middleware
        """
        self.app = app
        self.public_paths = public_paths or []
        self.exclude_paths = exclude_paths or []
    
    async def __call__(self, scope: Scope, receive: Receive, send: Send):
        """
        Método de llamada ASGI que procesa la solicitud.
        
        Args:
            scope: Información del ámbito de la solicitud
            receive: Canal para recibir mensajes
            send: Canal para enviar mensajes
        """
        # Solo procesar solicitudes HTTP
        if scope["type"] != "http":
            return await self.app(scope, receive, send)
            
        # Crear objeto Request para facilitar el acceso a la información
        request = Request(scope)
        path = request.url.path
        
        # Verificar si la ruta está excluida o es pública
        if self._is_excluded_path(path) or self._is_public_path(path):
            return await self.app(scope, receive, send)
        
        # Verificar autenticación
        auth_header = request.headers.get("Authorization")
        if not auth_header:
            # Enviar respuesta de error
            response = JSONResponse(
                status_code=status.HTTP_401_UNAUTHORIZED,
                content={"detail": "No se proporcionó token de autenticación"},
                headers={"WWW-Authenticate": "Bearer"}
            )
            return await response(scope, receive, send)
        
        # Obtener token del header
        parts = auth_header.split()
        if len(parts) != 2 or parts[0].lower() != "bearer":
            response = JSONResponse(
                status_code=status.HTTP_401_UNAUTHORIZED,
                content={"detail": "Formato de token inválido"},
                headers={"WWW-Authenticate": "Bearer"}
            )
            return await response(scope, receive, send)
        
        token = parts[1]
        
        # Verificar token
        try:
            # Decodificar el token
            payload = decode_token(token)
            
            # Verificar tipo de token
            token_type = payload.get("type", "")
            if token_type != "access":
                response = JSONResponse(
                    status_code=status.HTTP_401_UNAUTHORIZED,
                    content={"detail": "Tipo de token no válido"},
                    headers={"WWW-Authenticate": "Bearer"}
                )
                return await response(scope, receive, send)
            
            # Si es necesario, verificar si el usuario existe
            if settings.VERIFY_TOKEN_USER_EXISTS:
                db = SessionLocal()
                try:
                    from models.user import User
                    
                    user_id = int(payload.get("sub"))
                    user = db.query(User).filter(User.id == user_id, User.is_active == True).first()
                    
                    if not user:
                        response = JSONResponse(
                            status_code=status.HTTP_401_UNAUTHORIZED,
                            content={"detail": "Usuario no válido o inactivo"},
                            headers={"WWW-Authenticate": "Bearer"}
                        )
                        return await response(scope, receive, send)
                finally:
                    db.close()
            
            # Añadir información del usuario al scope para su uso posterior
            scope["user"] = payload
            
            # Continuar con la solicitud
            return await self.app(scope, receive, send)
            
        except JWTError:
            response = JSONResponse(
                status_code=status.HTTP_401_UNAUTHORIZED,
                content={"detail": "Token no válido o expirado"},
                headers={"WWW-Authenticate": "Bearer"}
            )
            return await response(scope, receive, send)
        except Exception:
            response = JSONResponse(
                status_code=status.HTTP_401_UNAUTHORIZED,
                content={"detail": "Error al procesar la autenticación"},
                headers={"WWW-Authenticate": "Bearer"}
            )
            return await response(scope, receive, send)
    
    def _is_public_path(self, path: str) -> bool:
        """
        Verifica si la ruta es pública.
        
        Args:
            path: Ruta de la solicitud
            
        Returns:
            bool: True si la ruta es pública
        """
        # Considerar siempre públicas las rutas de documentación y autenticación
        if path.startswith("/docs") or path.startswith("/redoc") or path.startswith("/openapi.json"):
            return True
        
        if path.startswith("/auth/login") or path.startswith("/auth/register"):
            return True
        
        # Verificar rutas públicas configuradas
        for public_path in self.public_paths:
            if path.startswith(public_path):
                return True
        
        return False
    
    def _is_excluded_path(self, path: str) -> bool:
        """
        Verifica si la ruta está excluida del middleware.
        
        Args:
            path: Ruta de la solicitud
            
        Returns:
            bool: True si la ruta está excluida
        """
        for excluded_path in self.exclude_paths:
            if path.startswith(excluded_path):
                return True
        
        return False