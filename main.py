from fastapi import FastAPI, Request, Depends
from fastapi.middleware.cors import CORSMiddleware
from fastapi.responses import JSONResponse
from fastapi.openapi.docs import get_swagger_ui_html
from contextlib import asynccontextmanager
import logging
import time
from typing import List

from config import settings
from database import engine, Base
from routes import auth, tokens
from middleware.auth_middleware import AuthMiddleware

# Configuración de logging
logging.basicConfig(
    level=logging.INFO,
    format="%(asctime)s - %(name)s - %(levelname)s - %(message)s",
)
logger = logging.getLogger("app")

# Lifespan para configurar la aplicación
@asynccontextmanager
async def lifespan(app: FastAPI):
    # Crear tablas al iniciar la aplicación
    logger.info("Inicializando la base de datos...")
    Base.metadata.create_all(bind=engine)
    logger.info("Base de datos inicializada")
    
    # Crear roles por defecto si no existen
    from models.role import Role
    from sqlalchemy.orm import Session
    from database import SessionLocal
    
    db = SessionLocal()
    try:
        # Verificar si existe el rol de administrador
        admin_role = db.query(Role).filter(Role.name == "admin").first()
        if not admin_role:
            admin_role = Role(name="admin", description="Administrador del sistema", is_default=False)
            db.add(admin_role)
        
        # Verificar si existe el rol de usuario
        user_role = db.query(Role).filter(Role.name == "user").first()
        if not user_role:
            user_role = Role(name="user", description="Usuario estándar", is_default=True)
            db.add(user_role)
        
        db.commit()
    except Exception as e:
        logger.error(f"Error al crear roles por defecto: {e}")
        db.rollback()
    finally:
        db.close()
    
    logger.info("Aplicación inicializada correctamente")
    yield
    logger.info("Aplicación finalizada")

# Crear la aplicación FastAPI
app = FastAPI(
    title=settings.API_NAME,
    version=settings.API_VERSION,
    description="API de autenticación y gestión de tokens",
    docs_url=None,  # Deshabilitar docs por defecto para personalizarlos
    redoc_url=None,  # Deshabilitar redoc por defecto
    lifespan=lifespan
)

# Configurar CORS
app.add_middleware(
    CORSMiddleware,
    allow_origins=settings.CORS_ORIGINS,  # Ahora es una propiedad que devuelve una lista
    allow_credentials=True,
    allow_methods=["*"],
    allow_headers=["*"],
)

# Definir rutas públicas (no requieren autenticación)
public_paths = [
    "/auth/login",
    "/auth/register",
    "/auth/verify-email",
    "/auth/refresh-token",
    "/docs",
    "/redoc",
    "/openapi.json"
]

# Agregar middleware de autenticación
# Solo se aplica a las rutas no incluidas en public_paths
app.add_middleware(
    AuthMiddleware,
    public_paths=public_paths
)

# Middleware para logging de tiempo de respuesta
@app.middleware("http")
async def add_process_time_header(request: Request, call_next):
    start_time = time.time()
    response = await call_next(request)
    process_time = time.time() - start_time
    response.headers["X-Process-Time"] = str(process_time)
    logger.debug(f"Tiempo de procesamiento: {process_time:.4f} segundos")
    return response

# Manejador de excepciones global
@app.exception_handler(Exception)
async def global_exception_handler(request: Request, exc: Exception):
    logger.error(f"Error no manejado: {exc}", exc_info=True)
    return JSONResponse(
        status_code=500,
        content={"detail": "Error interno del servidor"}
    )

# Registrar rutas
app.include_router(auth.router)
app.include_router(tokens.router)

# Ruta personalizada para la documentación Swagger
@app.get("/docs", include_in_schema=False)
async def custom_swagger_ui_html():
    return get_swagger_ui_html(
        openapi_url="/openapi.json",
        title=f"{settings.API_NAME} - Documentación API",
        swagger_favicon_url=""
    )

# Ruta de estado
@app.get("/health", tags=["system"])
async def health_check():
    return {"status": "ok", "version": settings.API_VERSION}

# Ruta principal
@app.get("/", tags=["system"])
async def root():
    return {
        "name": settings.API_NAME,
        "version": settings.API_VERSION,
        "description": "API de autenticación y gestión de tokens"
    }

if __name__ == "__main__":
    import uvicorn
    uvicorn.run("main:app", host="0.0.0.0", port=9000, reload=True)