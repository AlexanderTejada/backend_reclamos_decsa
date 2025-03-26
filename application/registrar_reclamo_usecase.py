#application/registrar_reclamo_usecase.py
from infrastructure.sqlalchemy_reclamo_repository import SQLAlchemyReclamoRepository
from infrastructure.sqlalchemy_usuario_repository import SQLAlchemyUsuarioRepository
from domain.entities import Cliente, Reclamo

class RegistrarReclamoUseCase:
    def __init__(self, reclamo_repository: SQLAlchemyReclamoRepository, usuario_repository: SQLAlchemyUsuarioRepository):
        self.reclamo_repository = reclamo_repository
        self.usuario_repository = usuario_repository

    def ejecutar(self, dni: str, descripcion: str):
        """Registra un reclamo para un cliente. Si no existe en DB2, lo copia desde DB1."""
        cliente = self.usuario_repository.obtener_por_dni(dni)
        if not cliente:
            cliente = self.usuario_repository.copiar_cliente_a_db2(dni)
            if not cliente:
                return {"error": "Cliente no encontrado en PR_CAU"}, 404

        # Crear el reclamo
        reclamo = Reclamo(
            ID_USUARIO=cliente.ID_USUARIO,
            DESCRIPCION=descripcion,
            ESTADO="Pendiente"
        )

        self.reclamo_repository.guardar(reclamo)

        return {
            "mensaje": "Reclamo registrado con éxito",
            "id_reclamo": reclamo.ID_RECLAMO,
            "cliente": {
                "nombre": cliente.NOMBRE_COMPLETO,
                "dni": cliente.DNI,
                "codigo_suministro": cliente.CODIGO_SUMINISTRO,
                "direccion": cliente.CALLE,
                "barrio": cliente.BARRIO
            }

        }, 201
