# infrastructure/database.py
from sqlalchemy import create_engine
from sqlalchemy.orm import sessionmaker
from infrastructure.settings import Config
import logging

logging.basicConfig(level=logging.INFO, format="%(asctime)s - %(levelname)s - %(message)s")

engine_db1 = create_engine(Config.SQLALCHEMY_BINDS["db1"], pool_size=10, max_overflow=20)
engine_db2 = create_engine(Config.SQLALCHEMY_BINDS["db2"], pool_size=10, max_overflow=20)

SessionLocal_db1 = sessionmaker(autocommit=False, autoflush=False, bind=engine_db1)
SessionLocal_db2 = sessionmaker(autocommit=False, autoflush=False, bind=engine_db2)

def init_db(app):
    app.engine_db1 = engine_db1
    app.engine_db2 = engine_db2
    logging.info("Bases de datos inicializadas con FastAPI")

def get_db_session(app=None, bind=None):
    if bind == "db1":
        return SessionLocal_db1()
    return SessionLocal_db2()

def get_db(bind: str = "db2"):
    if bind == "db1":
        db = SessionLocal_db1()
    else:
        db = SessionLocal_db2()
    try:
        yield db
    finally:
        db.close()