from sqlalchemy.orm import Session
from fastapi import Depends, HTTPException, status
from datetime import datetime
from typing import List, Optional, Dict, Any

from models.token import RefreshToken
from models.user import User
from utils.security import decode_token
from database import get_db
from config import settings

class TokenService:
    def __init__(self, db: Session):
        self.db = db
    
    def get_active_refresh_tokens(self, user_id: int) -> List[RefreshToken]:
        """
        Obtiene todos los tokens de refresco activos de un usuario.
        
        Args:
            user_id: ID del usuario
            
        Returns:
            List[RefreshToken]: Lista de tokens activos
        """
        return self.db.query(RefreshToken).filter(
            RefreshToken.user_id == user_id,
            RefreshToken.revoked == False,
            RefreshToken.expires_at > datetime.utcnow()
        ).all()
    
    def revoke_token(self, token: str, user_id: Optional[int] = None) -> bool:
        """
        Revoca un token de refresco.
        
        Args:
            token: Token a revocar
            user_id: ID del usuario (opcional, para verificar propiedad)
            
        Returns:
            bool: True si se revocó, False si no se encontró
        """
        query = self.db.query(RefreshToken).filter(
            RefreshToken.token == token,
            RefreshToken.revoked == False
        )
        
        if user_id:
            query = query.filter(RefreshToken.user_id == user_id)
        
        token_record = query.first()
        
        if not token_record:
            return False
        
        token_record.revoked = True
        token_record.revoked_at = datetime.utcnow()
        self.db.commit()
        
        return True
    
    def revoke_all_user_tokens(self, user_id: int) -> int:
        """
        Revoca todos los tokens de refresco de un usuario.
        
        Args:
            user_id: ID del usuario
            
        Returns:
            int: Número de tokens revocados
        """
        tokens = self.db.query(RefreshToken).filter(
            RefreshToken.user_id == user_id,
            RefreshToken.revoked == False
        ).all()
        
        count = 0
        for token in tokens:
            token.revoked = True
            token.revoked_at = datetime.utcnow()
            count += 1
        
        self.db.commit()
        return count
    
    def clean_expired_tokens(self) -> int:
        """
        Elimina los tokens expirados de la base de datos.
        
        Returns:
            int: Número de tokens eliminados
        """
        expired = self.db.query(RefreshToken).filter(
            RefreshToken.expires_at < datetime.utcnow()
        ).delete()
        
        self.db.commit()
        return expired
    
    def introspect_token(self, token: str) -> Dict[str, Any]:
        """
        Obtiene información detallada sobre un token.
        
        Args:
            token: Token a inspeccionar
            
        Returns:
            Dict[str, Any]: Información del token
            
        Raises:
            HTTPException: Si hay un error al decodificar el token
        """
        try:
            # Decodificar el token
            payload = decode_token(token)
            
            # Verificar si el token está en la base de datos (si es refresh token)
            token_type = payload.get("type", "")
            is_active = True
            
            if token_type == "refresh":
                refresh_token = self.db.query(RefreshToken).filter(
                    RefreshToken.token == token,
                    RefreshToken.revoked == False,
                    RefreshToken.expires_at > datetime.utcnow()
                ).first()
                
                is_active = refresh_token is not None
            
            # Obtener información del usuario
            user_id = int(payload.get("sub"))
            user = self.db.query(User).filter(User.id == user_id).first()
            
            if not user:
                is_active = False
            
            return {
                "active": is_active,
                "token_type": token_type,
                "exp": payload.get("exp"),
                "iat": payload.get("iat"),
                "jti": payload.get("jti"),
                "sub": payload.get("sub"),
                "username": payload.get("username"),
                "roles": payload.get("roles", [])
            }
            
        except Exception:
            return {"active": False}