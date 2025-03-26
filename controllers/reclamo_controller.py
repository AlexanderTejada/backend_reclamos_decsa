#controllers/reclamo_controller.py
from application.reclamo_service import ReclamoService
from flask import jsonify

class ReclamoController:
    def __init__(self, reclamo_service: ReclamoService):
        self.reclamo_service = reclamo_service

    def obtener_reclamos_con_clientes(self):
        """Obtiene todos los reclamos junto con la información del cliente."""
        reclamos, codigo = self.reclamo_service.obtener_reclamos()
        return jsonify(reclamos), codigo

    def crear_reclamo(self, dni, descripcion):
        """Crea un nuevo reclamo asociado a un cliente por su DNI."""
        resultado, codigo = self.reclamo_service.crear_reclamo(dni, descripcion)
        return jsonify(resultado), codigo

    def cancelar_reclamo(self, id_reclamo):
        """Permite cancelar un reclamo si está en estado 'Pendiente'."""
        resultado, codigo = self.reclamo_service.cancelar_reclamo(id_reclamo)
        return jsonify(resultado), codigo

    def actualizar_estado_reclamo(self, id_reclamo, nuevo_estado):
        """Actualiza el estado de un reclamo."""
        resultado, codigo = self.reclamo_service.actualizar_estado(id_reclamo, nuevo_estado)
        return jsonify(resultado), codigo
