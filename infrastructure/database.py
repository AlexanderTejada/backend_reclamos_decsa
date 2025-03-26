# infrastructure/database.py
from sqlalchemy import create_engine
from sqlalchemy.orm import sessionmaker
from infrastructure.settings import Config
import logging

logging.basicConfig(level=logging.INFO, format="%(asctime)s - %(levelname)s - %(message)s")

# Motores para cada base de datos
engine_db1 = create_engine(Config.SQLALCHEMY_BINDS["db1"], pool_size=10, max_overflow=20)
engine_db2 = create_engine(Config.SQLALCHEMY_BINDS["db2"], pool_size=10, max_overflow=20)

# Fábrica de sesiones
SessionLocal_db1 = sessionmaker(autocommit=False, autoflush=False, bind=engine_db1)
SessionLocal_db2 = sessionmaker(autocommit=False, autoflush=False, bind=engine_db2)

def init_db(app):
    """Inicializa las bases de datos para FastAPI."""
    app.engine_db1 = engine_db1
    app.engine_db2 = engine_db2
    logging.info("Bases de datos inicializadas con FastAPI")

def get_db_session(app=None, bind=None):
    """Retorna una sesión de base de datos para el bind especificado."""
    if bind == "db1":
        return SessionLocal_db1()
    return SessionLocal_db2()  # Por defecto, DB2