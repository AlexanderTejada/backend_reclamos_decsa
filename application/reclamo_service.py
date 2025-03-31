# reclamo_service.py
import logging
from application.registrar_reclamo_usecase import RegistrarReclamoUseCase
from application.consultar_estado_reclamo_usecase import ConsultarEstadoReclamoUseCase
from application.actualizar_estado_reclamo_usecase import ActualizarEstadoReclamoUseCase
from application.cancelar_reclamo_usecase import CancelarReclamoUseCase

logging.basicConfig(level=logging.INFO, format="%(asctime)s - %(levelname)s - %(message)s")

class ReclamoService:
    def __init__(self, registrar_reclamo_usecase: RegistrarReclamoUseCase, consultar_estado_usecase: ConsultarEstadoReclamoUseCase, actualizar_estado_usecase: ActualizarEstadoReclamoUseCase, cancelar_reclamo_usecase: CancelarReclamoUseCase):
        self.registrar_reclamo_usecase = registrar_reclamo_usecase
        self.consultar_estado_usecase = consultar_estado_usecase
        self.actualizar_estado_usecase = actualizar_estado_usecase
        self.cancelar_reclamo_usecase = cancelar_reclamo_usecase

    def crear_reclamo(self, dni, descripcion):
        """Crea un reclamo para un cliente."""
        return self.registrar_reclamo_usecase.ejecutar(dni, descripcion)

    def cancelar_reclamo(self, id_reclamo):
        """Permite cancelar un reclamo si está en estado 'Pendiente'."""
        return self.cancelar_reclamo_usecase.ejecutar(id_reclamo)

    def actualizar_estado(self, id_reclamo, nuevo_estado):
        """Actualiza el estado de un reclamo."""
        return self.actualizar_estado_usecase.ejecutar(id_reclamo, nuevo_estado)

    def obtener_reclamos(self, dni):
        """Obtiene todos los reclamos de un cliente por DNI."""
        return self.consultar_estado_usecase.ejecutar(dni)