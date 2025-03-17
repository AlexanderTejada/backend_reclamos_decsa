# app.py
from flask import Flask
from infrastructure.settings import Config
from infrastructure.extensions import cors
from domain.entities import db  # Importa la instancia db definida en entities.py
from routes.user_routes import user_bp
from routes.reclamo_routes import reclamo_bp

app = Flask(__name__)
app.config.from_object(Config)

# Inicializar extensiones
db.init_app(app)   # Configura SQLAlchemy con la app, pero no creamos tablas
cors.init_app(app) # Permite CORS

# Registrar blueprints con sus prefijos
app.register_blueprint(user_bp, url_prefix="/api/usuarios")
app.register_blueprint(reclamo_bp, url_prefix="/api/reclamos")

if __name__ == "__main__":
    app.run(debug=True)
