#controllers/user_controller.py
from application.usuario_service import UsuarioService
from flask import jsonify

class UsuarioController:
    def __init__(self, usuario_service: UsuarioService):
        self.usuario_service = usuario_service

    def obtener_cliente_por_dni(self, dni):
        """Obtiene un cliente por su DNI en DECSA_EXC."""
        resultado, codigo = self.usuario_service.obtener_usuario_por_dni(dni)
        return jsonify(resultado), codigo

    def copiar_cliente_a_db2(self, dni):
        """Copia un cliente desde PR_CAU a DECSA_EXC si no existe."""
        resultado, codigo = self.usuario_service.copiar_usuario_a_db2(dni)
        return jsonify(resultado), codigo

    def actualizar_cliente(self, dni, data):
        """Actualiza los datos de un cliente en DECSA_EXC."""
        resultado, codigo = self.usuario_service.actualizar_usuario(dni, data)
        return jsonify(resultado), codigo
