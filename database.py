from sqlalchemy import create_engine, text
from sqlalchemy.ext.declarative import declarative_base
from sqlalchemy.orm import sessionmaker
from sqlalchemy.pool import QueuePool
import mariadb
import urllib.parse
import logging

from config import settings

# Configurar logging
logger = logging.getLogger(__name__)

# Función para crear la base de datos si no existe
def create_database_if_not_exists():
    try:
        # Parsear la URL de conexión
        result = urllib.parse.urlparse(settings.DATABASE_URL)
        database_name = result.path.strip('/')
        
        # Crear una URL sin la base de datos para la conexión inicial
        server_url = f"{result.scheme}://{result.netloc}"
        
        # Reemplazar el dialecto si es necesario
        if server_url.startswith("mysql+mariadb"):
            server_url = server_url.replace("mysql+mariadb", "mysql+pymysql")
        
        # Crear un motor temporal para conectar al servidor sin especificar base de datos
        temp_engine = create_engine(server_url)
        
        # Verificar si la base de datos existe
        with temp_engine.connect() as conn:
            # Crear la base de datos si no existe
            conn.execute(text(f"CREATE DATABASE IF NOT EXISTS {database_name}"))
            logger.info(f"Base de datos '{database_name}' verificada/creada")
            
    except Exception as e:
        logger.error(f"Error al verificar/crear la base de datos: {e}")
        raise

# Intentar crear la base de datos
create_database_if_not_exists()

# Función para crear conexión a MariaDB
def get_mariadb_connection():
    # Parsear la URL de conexión para obtener los componentes
    result = urllib.parse.urlparse(settings.DATABASE_URL)
    params = urllib.parse.parse_qs(result.query)
    
    # Configurar la conexión a MariaDB
    conn = mariadb.connect(
        user=result.username,
        password=result.password,
        host=result.hostname,
        port=result.port or 3306,
        database=result.path.strip('/'),
        autocommit=False
    )
    return conn

# Creación del motor de base de datos con MariaDB
engine = create_engine(
    settings.DATABASE_URL.replace("mysql+mariadb", "mysql+pymysql") if settings.DATABASE_URL.startswith("mysql+mariadb") else settings.DATABASE_URL,
    pool_size=10,
    max_overflow=20,
    pool_timeout=30,
    pool_recycle=1800,
    pool_pre_ping=True,
    poolclass=QueuePool
)

# Creación de la sesión de base de datos
SessionLocal = sessionmaker(autocommit=False, autoflush=False, bind=engine)

# Clase base para los modelos
Base = declarative_base()

# Función para obtener una sesión de base de datos
def get_db():
    db = SessionLocal()
    try:
        yield db
    finally:
        db.close()