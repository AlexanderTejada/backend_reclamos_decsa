# routes/factura_routes.py
from fastapi import APIRouter, HTTPException
from infrastructure.sqlalchemy_usuario_repository import SQLAlchemyUsuarioRepository
from infrastructure.database import get_db_session  # Solo get_db_session
from application.consultar_facturas_usecase import ConsultarFacturasUseCase
import logging

logging.basicConfig(level=logging.INFO, format="%(asctime)s - %(levelname)s - %(message)s")

factura_router = APIRouter()

factura_repository = None
consultar_facturas_usecase = None

def init_factura_services(app):
    global factura_repository, consultar_facturas_usecase
    session_db1 = get_db_session(app, bind='db1')
    session_db2 = get_db_session(app, bind='db2')  # Cambiamos a get_db_session
    factura_repository = SQLAlchemyUsuarioRepository(session_db1, session_db2)
    consultar_facturas_usecase = ConsultarFacturasUseCase(factura_repository)

@factura_router.get("/{dni}")
async def obtener_facturas_por_dni(dni: str):
    global consultar_facturas_usecase
    if consultar_facturas_usecase is None:
        raise RuntimeError("Consultar facturas use case not initialized.")
    try:
        respuesta, codigo = consultar_facturas_usecase.ejecutar(dni)
        if codigo != 200:
            raise HTTPException(status_code=codigo, detail=respuesta.get("error", "Error desconocido"))
        return respuesta
    except Exception as e:
        raise HTTPException(status_code=500, detail=f"Error al consultar las facturas: {str(e)}")