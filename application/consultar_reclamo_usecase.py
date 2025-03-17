# application/consultar_reclamo_usecase.py
from infrastructure.sqlalchemy_reclamo_repository import SQLAlchemyReclamoRepository

class ConsultarReclamoUseCase:
    def __init__(self, reclamo_repository: SQLAlchemyReclamoRepository):
        self.reclamo_repository = reclamo_repository

    def ejecutar(self, id_reclamo: int):
        """Consulta un reclamo específico por su ID, incluyendo datos del usuario."""
        try:
            reclamo = self.reclamo_repository.obtener_por_id(id_reclamo)
            if not reclamo:
                return {"error": "Reclamo no encontrado"}, 404
            return reclamo.to_dict(), 200
        except Exception as e:
            return {"error": "Error al consultar el reclamo", "detalle": str(e)}, 500