# routes/reclamo_routes.py
from flask import Blueprint, request, jsonify
from infrastructure.sqlalchemy_reclamo_repository import SQLAlchemyReclamoRepository
from infrastructure.sqlalchemy_usuario_repository import SQLAlchemyUsuarioRepository
from infrastructure.database import db_session

from application.registrar_reclamo_usecase import RegistrarReclamoUseCase
from application.consultar_estado_reclamo_usecase import ConsultarEstadoReclamoUseCase
from application.consultar_reclamo_usecase import ConsultarReclamoUseCase

reclamo_bp = Blueprint("reclamos", __name__)

# Repositorios
reclamo_repository = SQLAlchemyReclamoRepository(db_session)
user_repository = SQLAlchemyUsuarioRepository(db_session)

# Casos de uso
registrar_reclamo_usecase = RegistrarReclamoUseCase(reclamo_repository, user_repository)
consultar_estado_usecase = ConsultarEstadoReclamoUseCase(reclamo_repository, user_repository)
consultar_reclamo_usecase = ConsultarReclamoUseCase(reclamo_repository)


###########################
# A) OBTENER TODOS
###########################
@reclamo_bp.route("/", methods=["GET"])
@reclamo_bp.route("", methods=["GET"])
def obtener_todos_los_reclamos():
    """
    Devuelve TODOS los reclamos en la DB2 (con info de usuario).
    Acepta:
      GET /api/reclamos   (sin barra final)
      GET /api/reclamos/  (con barra final)
    """
    try:
        # Asume que tienes un método listar_todos() en tu repositorio:
        reclamos = reclamo_repository.listar_todos()
        data = [r.to_dict() for r in reclamos]
        return jsonify(data), 200
    except Exception as e:
        return jsonify({"error": "Error al obtener todos los reclamos", "detalle": str(e)}), 500


###########################
# B) OBTENER RECLAMOS POR DNI
###########################
@reclamo_bp.route("/<dni>", methods=["GET"])
def obtener_reclamos_por_dni(dni):
    """
    Obtiene todos los reclamos de un usuario (DNI), con info de usuario.
    GET /api/reclamos/<dni>
    """
    try:
        respuesta, codigo = consultar_estado_usecase.ejecutar(dni)
        return jsonify(respuesta), codigo
    except Exception as e:
        return jsonify({"error": "Error al obtener los reclamos por DNI", "detalle": str(e)}), 500


###########################
# C) REGISTRAR RECLAMO POR DNI
###########################
@reclamo_bp.route("/<dni>", methods=["POST"])
def registrar_reclamo(dni):
    """
    Registra un reclamo para un usuario (DNI).
    POST /api/reclamos/<dni>
    Body: { "descripcion": "..." }
    """
    data = request.get_json()
    if not data or "descripcion" not in data:
        return jsonify({"error": "Descripción del reclamo requerida"}), 400

    try:
        respuesta, codigo = registrar_reclamo_usecase.ejecutar(dni, data["descripcion"])
        return jsonify(respuesta), codigo
    except Exception as e:
        return jsonify({"error": "Error al registrar el reclamo", "detalle": str(e)}), 500


###########################
# D) OBTENER RECLAMO POR ID
###########################
@reclamo_bp.route("/id/<int:id_reclamo>", methods=["GET"])
def obtener_reclamo_por_id(id_reclamo):
    """
    Obtiene un reclamo específico por ID.
    GET /api/reclamos/id/<id_reclamo>
    """
    try:
        respuesta, codigo = consultar_reclamo_usecase.ejecutar(id_reclamo)
        return jsonify(respuesta), codigo
    except ValueError:
        return jsonify({"error": "El id_reclamo debe ser un número válido"}), 400
    except Exception as e:
        return jsonify({"error": "Error al obtener reclamo por ID", "detalle": str(e)}), 500


###########################
# E) ACTUALIZAR ESTADO DE RECLAMO POR ID
###########################
@reclamo_bp.route("/<int:id_reclamo>", methods=["PUT"])
def actualizar_estado_reclamo(id_reclamo):
    """
    Actualiza el estado de un reclamo (ID).
    PUT /api/reclamos/<id_reclamo>
    Body: {"estado":"Pendiente/En proceso/Resuelto/etc"}
    """
    data = request.get_json()
    if not data or "estado" not in data:
        return jsonify({"error": "Se requiere el campo 'estado'"}), 400

    try:
        reclamo = reclamo_repository.obtener_por_id(id_reclamo)
        if not reclamo:
            return jsonify({"error": "Reclamo no encontrado"}), 404

        reclamo.ESTADO = data["estado"]
        db_session.commit()
        return jsonify({"mensaje": "Estado actualizado con éxito"}), 200

    except Exception as e:
        return jsonify({"error": "Error al actualizar el reclamo", "detalle": str(e)}), 500
