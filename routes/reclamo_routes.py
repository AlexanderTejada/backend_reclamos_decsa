# routes/reclamo_routes.py
from fastapi import APIRouter, HTTPException
from infrastructure.sqlalchemy_reclamo_repository import SQLAlchemyReclamoRepository
from infrastructure.sqlalchemy_usuario_repository import SQLAlchemyUsuarioRepository
from infrastructure.database import get_db_session  # Solo get_db_session
from application.registrar_reclamo_usecase import RegistrarReclamoUseCase
from application.consultar_estado_reclamo_usecase import ConsultarEstadoReclamoUseCase
from application.consultar_reclamo_usecase import ConsultarReclamoUseCase
import logging

logging.basicConfig(level=logging.INFO, format="%(asctime)s - %(levelname)s - %(message)s")

reclamo_router = APIRouter()

reclamo_repository = None
cliente_repository = None
registrar_reclamo_usecase = None
consultar_estado_usecase = None
consultar_reclamo_usecase = None

def init_reclamo_services(app):
    global reclamo_repository, cliente_repository, registrar_reclamo_usecase, consultar_estado_usecase, consultar_reclamo_usecase
    session_db1 = get_db_session(app, bind='db1')
    session_db2 = get_db_session(app, bind='db2')  # Cambiamos db_session por get_db_session

    if session_db1 is None or session_db2 is None:
        raise RuntimeError("Error en la inicialización de sesiones para DB1 o DB2.")

    reclamo_repository = SQLAlchemyReclamoRepository(session_db2)
    cliente_repository = SQLAlchemyUsuarioRepository(session_db1, session_db2)
    registrar_reclamo_usecase = RegistrarReclamoUseCase(reclamo_repository, cliente_repository)
    consultar_estado_usecase = ConsultarEstadoReclamoUseCase(reclamo_repository, cliente_repository)
    consultar_reclamo_usecase = ConsultarReclamoUseCase(reclamo_repository)

@reclamo_router.get("/")
async def obtener_todos_los_reclamos():
    global reclamo_repository
    if reclamo_repository is None:
        raise RuntimeError("Reclamo repository not initialized.")
    try:
        reclamos = reclamo_repository.listar_todos()
        data = [r.to_dict() for r in reclamos]
        return data
    except Exception as e:
        raise HTTPException(status_code=500, detail=f"Error al obtener los reclamos: {str(e)}")

@reclamo_router.get("/{dni}")
async def obtener_reclamos_por_dni(dni: str):
    global consultar_estado_usecase
    if consultar_estado_usecase is None:
        raise RuntimeError("Consultar estado use case not initialized.")
    try:
        respuesta, codigo = consultar_estado_usecase.ejecutar(dni)
        if codigo != 200:
            raise HTTPException(status_code=codigo, detail=respuesta.get("error", "Error desconocido"))
        return respuesta
    except Exception as e:
        raise HTTPException(status_code=500, detail=f"Error al consultar los reclamos por DNI: {str(e)}")

@reclamo_router.post("/{dni}")
async def registrar_reclamo(dni: str, data: dict):
    global registrar_reclamo_usecase
    if registrar_reclamo_usecase is None:
        raise RuntimeError("Registrar reclamo use case not initialized.")
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
async def obtener_reclamo_por_id(id_reclamo: int):
    global consultar_reclamo_usecase
    if consultar_reclamo_usecase is None:
        raise RuntimeError("Consultar reclamo use case not initialized.")
    try:
        respuesta, codigo = consultar_reclamo_usecase.ejecutar(id_reclamo)
        if codigo != 200:
            raise HTTPException(status_code=codigo, detail=respuesta.get("error", "Error desconocido"))
        return respuesta
    except Exception as e:
        raise HTTPException(status_code=500, detail=f"Error al obtener el reclamo por ID: {str(e)}")

@reclamo_router.put("/{id_reclamo}")
async def actualizar_estado_reclamo(id_reclamo: int, data: dict):
    global reclamo_repository
    if reclamo_repository is None:
        raise RuntimeError("Reclamo repository not initialized.")
    if not data or "estado" not in data:
        raise HTTPException(status_code=400, detail="El campo 'estado' es requerido")
    try:
        reclamo_actualizado = reclamo_repository.actualizar_estado(id_reclamo, data["estado"])
        if reclamo_actualizado is None:
            raise HTTPException(status_code=404, detail="Reclamo no encontrado")
        return {"mensaje": "Estado del reclamo actualizado exitosamente"}
    except Exception as e:
        raise HTTPException(status_code=500, detail=f"Error al actualizar el estado del reclamo: {str(e)}")