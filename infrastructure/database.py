#infraestucture/database.py
from flask_sqlalchemy import SQLAlchemy
from sqlalchemy.orm import scoped_session, sessionmaker
from flask import Flask
from infrastructure.settings import Config

# 🔹 Crear la aplicación Flask y el objeto SQLAlchemy
app = Flask(__name__)
app.config.from_object(Config)
db = SQLAlchemy(app)

# 🔹 Crear la sesión correctamente dentro del contexto de la aplicación
with app.app_context():
    SessionLocal = scoped_session(sessionmaker(autocommit=False, autoflush=False, bind=db.engine))

def get_db_session():
    """Retorna una sesión de base de datos."""
    session = SessionLocal()
    try:
        yield session
    finally:
        session.close()

# 🔹 Crear la sesión global para ser utilizada en los repositorios
db_session = SessionLocal
