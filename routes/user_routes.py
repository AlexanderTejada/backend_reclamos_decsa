# routes/user_routes.py
from flask import Blueprint, jsonify, request
from application.actualizar_usuario_usecase import ActualizarUsuarioUseCase
from infrastructure.sqlalchemy_usuario_repository import SQLAlchemyUsuarioRepository
from infrastructure.database import db_session
from domain.entities import db, UsuarioDB1, UsuarioDB2, Reclamo

user_bp = Blueprint("usuarios", __name__)

# Inicializar repositorios y casos de uso
user_repository = SQLAlchemyUsuarioRepository(db_session)
actualizar_usuario_usecase = ActualizarUsuarioUseCase(user_repository)

@user_bp.route("/<dni>", methods=["GET"])
def validar_usuario(dni):
    """Valida si el usuario existe en DECSA_DB2."""
    try:
        usuario = user_repository.obtener_por_dni(dni)
        if not usuario:
            return jsonify({"error": "Usuario no encontrado"}), 404
        return jsonify(usuario.to_dict())
    except Exception as e:
        return jsonify({"error": "Error al validar usuario", "detalle": str(e)}), 500

@user_bp.route("/<dni>", methods=["PUT"])
def actualizar_datos_usuario(dni):
    """Actualiza los datos de un usuario existente, copiándolo desde DECSA_DB1 si no existe en DECSA_DB2."""
    data = request.get_json()
    if not data:
        return jsonify({"error": "Datos de actualización requeridos"}), 400

    try:
        # Verificar si el usuario existe en DECSA_DB2
        usuario = user_repository.obtener_por_dni(dni)
        if not usuario:
            # Si no existe, buscar en DECSA_DB1
            usuario_db1 = user_repository.obtener_de_db1(dni)
            if not usuario_db1:
                return jsonify({"error": "Usuario no encontrado en DECSA_DB1"}), 404

            # Copiar el usuario a DECSA_DB2
            usuario = UsuarioDB2(
                COD_USER=usuario_db1.COD_USER,
                DNI=usuario_db1.DNI,
                MAIL=usuario_db1.MAIL,
                CELULAR=usuario_db1.CELULAR,
                FEC_ADD=usuario_db1.FEC_ADD,
                APELLIDO=usuario_db1.APELLIDO,
                FEC_VALIDACION=usuario_db1.FEC_VALIDACION,
                NOMBRE=usuario_db1.NOMBRE,
                NUMERO_SUMINISTRO=usuario_db1.NUMERO_SUMINISTRO,
                NUMERO_MEDIDOR=usuario_db1.NUMERO_MEDIDOR,
                DIRECCION=usuario_db1.DIRECCION
            )
            user_repository.guardar_en_db2(usuario)

        # Ahora que el usuario existe en DECSA_DB2, actualizar los datos
        respuesta = actualizar_usuario_usecase.ejecutar(dni, data)
        return jsonify({"mensaje": respuesta})
    except Exception as e:
        return jsonify({"error": "Error al actualizar datos", "detalle": str(e)}), 500