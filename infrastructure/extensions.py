#infraestructure/extensions.py
from flask_sqlalchemy import SQLAlchemy
from flask_cors import CORS

# Inicializar SQLAlchemy y CORS sin crear la app aún
db = SQLAlchemy()
cors = CORS()
