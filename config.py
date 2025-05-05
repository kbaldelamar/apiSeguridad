import os
from pydantic_settings import BaseSettings, SettingsConfigDict
from dotenv import load_dotenv
from datetime import timedelta
from typing import List

# Cargar variables de entorno desde el archivo .env
load_dotenv()

def read_secret_file(file_path):
    """Lee un secreto desde un archivo si existe, de lo contrario retorna None"""
    try:
        if os.path.exists(file_path):
            with open(file_path, 'r') as f:
                return f.read().strip()
        return None
    except Exception:
        return None

class Settings(BaseSettings):
    # Nombre y versión de la API
    API_NAME: str = "Auth API"
    API_VERSION: str = "1.0.0"
    
    # Configuración de la base de datos
    DATABASE_URL: str = os.getenv("DATABASE_URL", "mysql+mariadb://genoma:SALUD@localhost:13319/auth_db")
    USE_MARIADB_CONNECTOR: bool = os.getenv("USE_MARIADB_CONNECTOR", "True").lower() in ("true", "1", "t")

    # Configuración de seguridad
    SECRET_KEY: str = read_secret_file("/run/secrets/secret_key") or os.getenv("SECRET_KEY", "insecure-secret-key")
    ACCESS_TOKEN_ALGORITHM: str = "HS256"
    ACCESS_TOKEN_EXPIRE_MINUTES: int = int(os.getenv("ACCESS_TOKEN_EXPIRE_MINUTES", "30"))
    REFRESH_TOKEN_EXPIRE_DAYS: int = int(os.getenv("REFRESH_TOKEN_EXPIRE_DAYS", "7"))
    
    # Configuraciones de CORS - Ahora declaramos el campo correctamente
    CORS_ORIGINS_STR: str = os.getenv("CORS_ORIGINS", "*")
    
    # Configuraciones de Rate Limiting
    RATE_LIMIT_PER_MINUTE: int = int(os.getenv("RATE_LIMIT_PER_MINUTE", "60"))
    
    # Verificar usuario en el middleware
    VERIFY_TOKEN_USER_EXISTS: bool = os.getenv("VERIFY_TOKEN_USER_EXISTS", "False").lower() in ("true", "1", "t")
    
    # Configuraciones para OAuth (si se necesita en el futuro)
    OAUTH_PROVIDERS: dict = {}
    
    # Path para logs
    LOG_PATH: str = os.getenv("LOG_PATH", "./logs")
    
    # Configuración para pydantic 2.x
    model_config = SettingsConfigDict(
        env_file=".env",
        case_sensitive=True,
        extra="ignore"  # Permite campos extra
    )

    @property
    def access_token_expires(self) -> timedelta:
        return timedelta(minutes=self.ACCESS_TOKEN_EXPIRE_MINUTES)
    
    @property
    def refresh_token_expires(self) -> timedelta:
        return timedelta(days=self.REFRESH_TOKEN_EXPIRE_DAYS)
    
    @property
    def CORS_ORIGINS(self) -> List[str]:
        """
        Transforma la cadena de CORS_ORIGINS en una lista.
        """
        if self.CORS_ORIGINS_STR == "*":
            return ["*"]
        return [origin.strip() for origin in self.CORS_ORIGINS_STR.split(",") if origin.strip()]

# Instancia de configuración para usar en toda la aplicación
settings = Settings()