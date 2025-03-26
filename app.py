# app.py
from fastapi import FastAPI
from infrastructure.settings import Config
from infrastructure.extensions import init_cors
from infrastructure.database import init_db
from routes.user_routes import cliente_router as user_router, init_cliente_services
from routes.reclamo_routes import reclamo_router, init_reclamo_services
from routes.factura_routes import factura_router, init_factura_services
import logging
import os

logging.basicConfig(level=logging.INFO, format="%(asctime)s - %(levelname)s - %(message)s")

def create_app():
    app = FastAPI(
        title="DECSA API",
        description="API para gestión de reclamos y facturas",
        version="1.0.0"
    )
    app.config = Config

    init_db(app)
    init_cors(app)  # Configuramos CORS aquí

    app.include_router(user_router, prefix="/api/usuarios")
    app.include_router(reclamo_router, prefix="/api/reclamos")
    app.include_router(factura_router, prefix="/api/facturas")

    init_cliente_services(app)
    init_reclamo_services(app)
    init_factura_services(app)

    return app

if __name__ == "__main__":
    try:
        app = create_app()
        host = os.getenv("FASTAPI_HOST", "0.0.0.0")
        port = int(os.getenv("FASTAPI_PORT", 5000))
        logging.info(f"✅ Servidor FastAPI iniciado en {host}:{port}")
        import uvicorn
        uvicorn.run(app, host=host, port=port)
    except Exception as e:
        logging.error(f"❌ Error al iniciar la aplicación: {str(e)}")