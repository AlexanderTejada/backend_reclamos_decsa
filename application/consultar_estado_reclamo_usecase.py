#application/consultar_estado_reclamo_usecase.py
from infrastructure.sqlalchemy_reclamo_repository import SQLAlchemyReclamoRepository
from infrastructure.sqlalchemy_usuario_repository import SQLAlchemyUsuarioRepository

class ConsultarEstadoReclamoUseCase:
    def __init__(self, reclamo_repository: SQLAlchemyReclamoRepository, usuario_repository: SQLAlchemyUsuarioRepository):
        self.reclamo_repository = reclamo_repository
        self.usuario_repository = usuario_repository

    def ejecutar(self, dni: str):
        """Consulta todos los reclamos de un cliente a partir de su DNI."""
        cliente = self.usuario_repository.obtener_por_dni(dni)
        if not cliente:
            return {"error": "Cliente no encontrado"}, 404

        reclamos = self.reclamo_repository.obtener_por_usuario(cliente.ID_USUARIO)
        if not reclamos:
            return {"mensaje": "No tienes reclamos registrados"}, 200

        return {
            "cliente": {
                "nombre": cliente.NOMBRE_COMPLETO,
                "dni": cliente.DNI,
                "direccion": cliente.CALLE,
                "barrio": cliente.BARRIO,
                "codigo_suministro": cliente.CODIGO_SUMINISTRO
            },
            "reclamos": [reclamo.to_dict() for reclamo in reclamos]
        }, 200