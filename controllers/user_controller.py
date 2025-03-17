#controllers/ user_controller.py
from application.usuario_service import UsuarioService
from flask import jsonify

class UsuarioController:
    def __init__(self, usuario_service: UsuarioService):
        self.usuario_service = usuario_service

    def obtener_usuario_por_dni(self, dni):
        """Obtiene un usuario por su DNI en DECSA_DB2."""
        usuario = self.usuario_service.obtener_usuario_por_dni(dni)
        if not usuario:
            return jsonify({"error": "Usuario no encontrado"}), 404
        return jsonify(usuario)

    def copiar_usuario_a_db2(self, dni):
        """Copia un usuario desde DECSA_DB1 a DECSA_DB2 si no existe."""
        resultado, codigo = self.usuario_service.copiar_usuario_a_db2(dni)
        return jsonify(resultado), codigo

    def actualizar_usuario(self, dni, data):
        """Actualiza los datos de un usuario en DECSA_DB2."""
        resultado, codigo = self.usuario_service.actualizar_usuario(dni, data)
        return jsonify(resultado), codigo