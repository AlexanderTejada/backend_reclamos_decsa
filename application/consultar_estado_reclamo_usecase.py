#application/ consultar_estado_reclamo_usecase.py
from infrastructure.sqlalchemy_reclamo_repository import SQLAlchemyReclamoRepository
from infrastructure.sqlalchemy_usuario_repository import SQLAlchemyUsuarioRepository

class ConsultarEstadoReclamoUseCase:
    def __init__(self, reclamo_repository: SQLAlchemyReclamoRepository, usuario_repository: SQLAlchemyUsuarioRepository):
        self.reclamo_repository = reclamo_repository
        self.usuario_repository = usuario_repository

    def ejecutar(self, dni: str):
        """Consulta el estado de los reclamos de un usuario."""
        usuario = self.usuario_repository.obtener_por_dni(dni)
        if not usuario:
            return {"error": "Usuario no encontrado"}, 404

        reclamos = self.reclamo_repository.obtener_por_usuario(usuario.COD_USER)
        if not reclamos:
            return {"mensaje": "No tienes reclamos registrados"}, 200

        return {"reclamos": [reclamo.to_dict() for reclamo in reclamos]}, 200
