# routes/user_routes.py
from fastapi import APIRouter, HTTPException
from application.actualizar_usuario_usecase import ActualizarUsuarioUseCase
from infrastructure.sqlalchemy_usuario_repository import SQLAlchemyUsuarioRepository
from infrastructure.database import get_db_session
import logging

logging.basicConfig(level=logging.INFO, format="%(asctime)s - %(levelname)s - %(message)s")

cliente_router = APIRouter()

cliente_repository = None
actualizar_cliente_usecase = None

def init_cliente_services(app):
    global cliente_repository, actualizar_cliente_usecase
    session_db1 = get_db_session(app, bind='db1')
    session_db2 = get_db_session(app, bind='db2')
    cliente_repository = SQLAlchemyUsuarioRepository(session_db1, session_db2)
    actualizar_cliente_usecase = ActualizarUsuarioUseCase(cliente_repository)

@cliente_router.get("/{dni}")
async def validar_cliente(dni: str):
    """Valida si el cliente existe, buscando primero en DECSA_EXC (DB2) y luego en PR_CAU (DB1)."""
    global cliente_repository
    if cliente_repository is None:
        raise RuntimeError("Cliente repository not initialized. Call init_cliente_services first.")
    try:
        logging.info(f"Validando cliente con DNI: {dni}")
        # Buscar primero en DECSA_EXC (DB2)
        cliente_db2 = cliente_repository.obtener_por_dni(dni)
        if cliente_db2:
            logging.info(f"Cliente encontrado en DECSA_EXC: {cliente_db2.NOMBRE_COMPLETO}")
            return cliente_db2.to_dict()

        # Si no está en DB2, buscar en PR_CAU (DB1)
        cliente_db1 = cliente_repository.obtener_de_db1(dni)
        if cliente_db1:
            logging.info(f"Cliente encontrado en PR_CAU")
            return {
                "DNI": cliente_db1["Dni"],
                "NombreCompleto": cliente_db1["Nombre"],
                "CodigoSuministro": cliente_db1["CodigoSuministro"],
                "NumeroMedidor": cliente_db1["NumeroMedidor"],
                "Calle": cliente_db1["Calle"],
                "Barrio": cliente_db1["Barrio"],
                "Telefono": cliente_db1.get("Telefono"),
                "CodigoPostal": cliente_db1.get("CodigoPostal")
            }

        logging.warning(f"Cliente con DNI {dni} no encontrado en ninguna base")
        raise HTTPException(status_code=404, detail="Cliente no encontrado")
    except Exception as e:
        logging.error(f"Error al validar cliente: {str(e)}")
        raise HTTPException(status_code=500, detail=f"Error al validar cliente: {str(e)}")

@cliente_router.put("/{dni}")
async def actualizar_datos_cliente(dni: str, data: dict):
    """Actualiza los datos de un cliente existente o lo copia desde PR_CAU si no existe en DECSA_EXC."""
    global actualizar_cliente_usecase
    if actualizar_cliente_usecase is None:
        raise RuntimeError("Update use case not initialized. Call init_cliente_services first.")
    if not data:
        raise HTTPException(status_code=400, detail="Datos de actualización requeridos")
    try:
        logging.info(f"Actualizando cliente con DNI: {dni}")
        respuesta, status_code = actualizar_cliente_usecase.ejecutar(dni, data)
        if status_code != 200:
            raise HTTPException(status_code=status_code, detail=respuesta.get("error", "Error desconocido"))
        return respuesta
    except Exception as e:
        logging.error(f"Error al actualizar datos del cliente: {str(e)}")
        raise HTTPException(status_code=500, detail=f"Error al actualizar datos: {str(e)}")