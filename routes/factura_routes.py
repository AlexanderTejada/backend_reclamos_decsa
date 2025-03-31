# routes/factura_routes.py
from fastapi import APIRouter, HTTPException, Depends
from infrastructure.sqlalchemy_usuario_repository import SQLAlchemyUsuarioRepository
from infrastructure.database import get_db_session
from application.consultar_facturas_usecase import ConsultarFacturasUseCase
import logging

logging.basicConfig(level=logging.INFO, format="%(asctime)s - %(levelname)s - %(message)s")

factura_router = APIRouter()

# Instancias globales para las sesiones y repositorios
_session_db1 = None
_session_db2 = None
_factura_repository = None
_consultar_facturas_usecase = None

def init_factura_services(app):
    global _session_db1, _session_db2, _factura_repository, _consultar_facturas_usecase
    _session_db1 = get_db_session(app, bind='db1')
    _session_db2 = get_db_session(app, bind='db2')
    _factura_repository = SQLAlchemyUsuarioRepository(_session_db1, _session_db2)
    _consultar_facturas_usecase = ConsultarFacturasUseCase(_factura_repository)

def get_factura_repository():
    if _factura_repository is None:
        raise RuntimeError("Factura repository not initialized.")
    return _factura_repository

def get_consultar_facturas_usecase():
    if _consultar_facturas_usecase is None:
        raise RuntimeError("Consultar facturas use case not initialized.")
    return _consultar_facturas_usecase

@factura_router.get("/{dni}")
async def obtener_facturas_por_dni(dni: str, consultar_facturas_usecase: ConsultarFacturasUseCase = Depends(get_consultar_facturas_usecase)):
    try:
        respuesta, status_code = consultar_facturas_usecase.ejecutar(dni)
        if status_code != 200:
            raise HTTPException(status_code=status_code, detail=respuesta.get("error", "Error desconocido"))
        return respuesta
    except Exception as e:
        raise HTTPException(status_code=500, detail=f"Error al consultar las facturas: {str(e)}")