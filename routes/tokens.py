from fastapi import APIRouter, Depends, HTTPException, status, Security
from sqlalchemy.orm import Session
from typing import List, Dict, Any

from database import get_db
from services.token import TokenService
from schemas.token import TokenIntrospection, RevokeTokenRequest
from dependencies.auth import get_current_user

router = APIRouter(prefix="/tokens", tags=["tokens"])

@router.post("/introspect", response_model=TokenIntrospection)
async def introspect_token(
    token: str,
    db: Session = Depends(get_db)
):
    """
    Inspecciona un token para verificar su validez y obtener información.
    """
    token_service = TokenService(db)
    token_info = token_service.introspect_token(token)
    
    return TokenIntrospection(
        active=token_info.get("active", False),
        token_type=token_info.get("token_type"),
        exp=token_info.get("exp"),
        iat=token_info.get("iat"),
        jti=token_info.get("jti"),
        sub=token_info.get("sub"),
        username=token_info.get("username"),
        aud=[],
        iss=None,
        nbf=None,
        client_id=None,
        scope=None
    )

@router.post("/revoke", status_code=status.HTTP_204_NO_CONTENT)
async def revoke_token(
    token_data: RevokeTokenRequest,
    current_user: Dict[str, Any] = Security(get_current_user),
    db: Session = Depends(get_db)
):
    """
    Revoca un token específico.
    """
    token_service = TokenService(db)
    user_id = int(current_user.get("sub"))
    
    success = token_service.revoke_token(token_data.token, user_id)
    if not success:
        raise HTTPException(
            status_code=status.HTTP_400_BAD_REQUEST,
            detail="Token inválido o no pertenece al usuario"
        )
    
    return None

@router.post("/revoke-all", status_code=status.HTTP_204_NO_CONTENT)
async def revoke_all_tokens(
    current_user: Dict[str, Any] = Security(get_current_user),
    db: Session = Depends(get_db)
):
    """
    Revoca todos los tokens del usuario actual.
    """
    token_service = TokenService(db)
    user_id = int(current_user.get("sub"))
    
    token_service.revoke_all_user_tokens(user_id)
    
    return None

@router.get("/active", response_model=List[Dict[str, Any]])
async def get_active_tokens(
    current_user: Dict[str, Any] = Security(get_current_user),
    db: Session = Depends(get_db)
):
    """
    Obtiene todos los tokens activos del usuario actual.
    """
    token_service = TokenService(db)
    user_id = int(current_user.get("sub"))
    
    tokens = token_service.get_active_refresh_tokens(user_id)
    
    return [
        {
            "id": token.id,
            "created_at": token.created_at,
            "expires_at": token.expires_at,
            "user_agent": token.user_agent,
            "ip_address": token.ip_address
        }
        for token in tokens
    ]