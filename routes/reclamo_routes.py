# routes/reclamo_routes.py
from fastapi import APIRouter, HTTPException, Depends
from infrastructure.sqlalchemy_reclamo_repository import SQLAlchemyReclamoRepository
from infrastructure.sqlalchemy_usuario_repository import SQLAlchemyUsuarioRepository
from infrastructure.database import get_db_session
from application.registrar_reclamo_usecase import RegistrarReclamoUseCase
from application.consultar_estado_reclamo_usecase import ConsultarEstadoReclamoUseCase
from application.consultar_reclamo_usecase import ConsultarReclamoUseCase
import logging

logging.basicConfig(level=logging.INFO, format="%(asctime)s - %(levelname)s - %(message)s")

reclamo_router = APIRouter()

# Instancias globales para las sesiones y repositorios
_session_db1 = None
_session_db2 = None
_reclamo_repository = None
_cliente_repository = None
_registrar_reclamo_usecase = None
_consultar_estado_usecase = None
_consultar_reclamo_usecase = None

def init_reclamo_services(app):
    global _session_db1, _session_db2, _reclamo_repository, _cliente_repository
    global _registrar_reclamo_usecase, _consultar_estado_usecase, _consultar_reclamo_usecase
    _session_db1 = get_db_session(app, bind='db1')
    _session_db2 = get_db_session(app, bind='db2')
    if _session_db1 is None or _session_db2 is None:
        raise RuntimeError("Error en la inicialización de sesiones para DB1 o DB2.")
    _reclamo_repository = SQLAlchemyReclamoRepository(_session_db2)
    _cliente_repository = SQLAlchemyUsuarioRepository(_session_db1, _session_db2)
    _registrar_reclamo_usecase = RegistrarReclamoUseCase(_reclamo_repository, _cliente_repository)
    _consultar_estado_usecase = ConsultarEstadoReclamoUseCase(_reclamo_repository, _cliente_repository)
    _consultar_reclamo_usecase = ConsultarReclamoUseCase(_reclamo_repository)

# Dependencias para inyectar en las rutas
def get_reclamo_repository():
    if _reclamo_repository is None:
        raise RuntimeError("Reclamo repository not initialized.")
    return _reclamo_repository

def get_registrar_reclamo_usecase():
    if _registrar_reclamo_usecase is None:
        raise RuntimeError("Registrar reclamo use case not initialized.")
    return _registrar_reclamo_usecase

def get_consultar_estado_usecase():
    if _consultar_estado_usecase is None:
        raise RuntimeError("Consultar estado use case not initialized.")
    return _consultar_estado_usecase

def get_consultar_reclamo_usecase():
    if _consultar_reclamo_usecase is None:
        raise RuntimeError("Consultar reclamo use case not initialized.")
    return _consultar_reclamo_usecase

@reclamo_router.get("/")
async def obtener_todos_los_reclamos(reclamo_repository: SQLAlchemyReclamoRepository = Depends(get_reclamo_repository)):
    try:
        reclamos = reclamo_repository.listar_todos()
        data = [r.to_dict() for r in reclamos]
        return data
    except Exception as e:
        raise HTTPException(status_code=500, detail=f"Error al obtener los reclamos: {str(e)}")

@reclamo_router.get("/{dni}")
async def obtener_reclamos_por_dni(dni: str, consultar_estado_usecase: ConsultarEstadoReclamoUseCase = Depends(get_consultar_estado_usecase)):
    try:
        respuesta, codigo = consultar_estado_usecase.ejecutar(dni)
        if codigo != 200:
            raise HTTPException(status_code=codigo, detail=respuesta.get("error", "Error desconocido"))
        return respuesta
    except Exception as e:
        raise HTTPException(status_code=500, detail=f"Error al consultar los reclamos por DNI: {str(e)}")

@reclamo_router.post("/{dni}")
async def registrar_reclamo(dni: str, data: dict, registrar_reclamo_usecase: RegistrarReclamoUseCase = Depends(get_registrar_reclamo_usecase)):
    if not data or "descripcion" not in data:
        raise HTTPException(status_code=400, detail="La descripción del reclamo es requerida")
    try:
        respuesta, codigo = registrar_reclamo_usecase.ejecutar(dni, data["descripcion"])
        if codigo != 201:
            raise HTTPException(status_code=codigo, detail=respuesta.get("error", "Error desconocido"))
        return respuesta
    except Exception as e:
        raise HTTPException(status_code=500, detail=f"Error al registrar el reclamo: {str(e)}")

@reclamo_router.get("/id/{id_reclamo}")
async def obtener_reclamo_por_id(id_reclamo: int, consultar_reclamo_usecase: ConsultarReclamoUseCase = Depends(get_consultar_reclamo_usecase)):
    try:
        respuesta, codigo = consultar_reclamo_usecase.ejecutar(id_reclamo)
        if codigo != 200:
            raise HTTPException(status_code=codigo, detail=respuesta.get("error", "Error desconocido"))
        return respuesta
    except Exception as e:
        raise HTTPException(status_code=500, detail=f"Error al obtener el reclamo por ID: {str(e)}")

@reclamo_router.put("/{id_reclamo}")
async def actualizar_estado_reclamo(id_reclamo: int, data: dict, reclamo_repository: SQLAlchemyReclamoRepository = Depends(get_reclamo_repository)):
    if not data or "estado" not in data:
        raise HTTPException(status_code=400, detail="El campo 'estado' es requerido")
    try:
        reclamo_actualizado = reclamo_repository.actualizar_estado(id_reclamo, data["estado"])
        if reclamo_actualizado is None:
            raise HTTPException(status_code=404, detail="Reclamo no encontrado")
        return {"mensaje": "Estado del reclamo actualizado exitosamente"}
    except Exception as e:
        raise HTTPException(status_code=500, detail=f"Error al actualizar el estado del reclamo: {str(e)}")