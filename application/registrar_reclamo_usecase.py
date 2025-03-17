# application/registrar_reclamo_usecase.py
from infrastructure.sqlalchemy_reclamo_repository import SQLAlchemyReclamoRepository
from infrastructure.sqlalchemy_usuario_repository import SQLAlchemyUsuarioRepository
from domain.entities import UsuarioDB1, UsuarioDB2
from domain.entities import Reclamo


class RegistrarReclamoUseCase:
    def __init__(self, reclamo_repository: SQLAlchemyReclamoRepository, usuario_repository: SQLAlchemyUsuarioRepository):
        self.reclamo_repository = reclamo_repository
        self.usuario_repository = usuario_repository

    def ejecutar(self, dni: str, descripcion: str):
        """Registra un reclamo para un usuario, copiándolo desde DECSA_DB1 si no existe en DECSA_DB2."""
        # Verificar si el usuario existe en DECSA_DB2
        usuario = self.usuario_repository.obtener_por_dni(dni)
        if not usuario:
            # Si no existe, buscar en DECSA_DB1
            usuario_db1 = self.usuario_repository.obtener_de_db1(dni)
            if not usuario_db1:
                return {"error": "Usuario no encontrado en DECSA_DB1"}, 404

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
            self.usuario_repository.guardar_en_db2(usuario)

        # Crear el reclamo
        reclamo = Reclamo(
            ID_RECLAMO=None,  # El ID será generado por la base de datos
            COD_USER=usuario.COD_USER,
            DESCRIPCION=descripcion
        )
        reclamo = self.reclamo_repository.guardar(reclamo)
        return {"mensaje": "Reclamo registrado con éxito", "id_reclamo": reclamo.ID_RECLAMO}, 201