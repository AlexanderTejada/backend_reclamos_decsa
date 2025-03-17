#application/reclamo_service.py
import logging
from domain.entities import UsuarioDB1, UsuarioDB2
from infrastructure.sqlalchemy_reclamo_repository import SQLAlchemyReclamoRepository
from infrastructure.sqlalchemy_usuario_repository import SQLAlchemyUsuarioRepository


class ReclamoService:
    def __init__(self, reclamo_repo: SQLAlchemyReclamoRepository, usuario_repo: SQLAlchemyUsuarioRepository):
        self.reclamo_repo = reclamo_repo
        self.usuario_repo = usuario_repo

    def crear_reclamo(self, dni, descripcion):
        """Crea un reclamo. Si el usuario no existe en DB2, lo copia desde DB1."""
        logging.info(f"Intentando crear reclamo para DNI: {dni}")

        # 🔹 Buscar usuario en DB2
        usuario = self.usuario_repo.obtener_por_dni(dni)

        # 🔹 Si no está en DB2, buscar en DB1 y copiarlo a DB2
        if not usuario:
            logging.warning(f"Usuario con DNI {dni} no encontrado en DB2. Buscando en DB1...")
            usuario = self.usuario_repo.obtener_de_db1(dni)
            if not usuario:
                logging.error(f"Usuario con DNI {dni} no encontrado en DB1")
                return {"error": "Usuario no encontrado"}, 404

            # Copiar usuario de DB1 a DB2
            usuario_db2 = UsuarioDB2(
                COD_USER=usuario.COD_USER,
                DNI=usuario.DNI,
                MAIL=usuario.MAIL,
                CELULAR=usuario.CELULAR,
                FEC_ADD=usuario.FEC_ADD,
                APELLIDO=usuario.APELLIDO,
                FEC_VALIDACION=usuario.FEC_VALIDACION,
                NOMBRE=usuario.NOMBRE,
                NUMERO_SUMINISTRO=usuario.NUMERO_SUMINISTRO,
                NUMERO_MEDIDOR=usuario.NUMERO_MEDIDOR,
                DIRECCION=usuario.DIRECCION
            )
            self.usuario_repo.guardar_en_db2(usuario_db2)
            usuario = usuario_db2  # Ahora usuario es el que está en DB2
            logging.info(f"Usuario con DNI {dni} copiado exitosamente a DB2")

        # 🔹 Crear el reclamo
        nuevo_reclamo = Reclamo(
            COD_USER=usuario.COD_USER,
            DESCRIPCION=descripcion,
            ESTADO="Pendiente"
        )

        self.reclamo_repo.guardar(nuevo_reclamo)
        logging.info(f"Reclamo creado exitosamente para usuario {usuario.NOMBRE} {usuario.APELLIDO}")

        return {
            "ID_RECLAMO": nuevo_reclamo.ID_RECLAMO,
            "DESCRIPCION": nuevo_reclamo.DESCRIPCION,
            "ESTADO": nuevo_reclamo.ESTADO,
            "FECHA_RECLAMO": nuevo_reclamo.FECHA_RECLAMO,
            "NOMBRE": usuario.NOMBRE,
            "APELLIDO": usuario.APELLIDO,
            "DNI": usuario.DNI,
            "DIRECCION": usuario.DIRECCION
        }, 201

    def cancelar_reclamo(self, id_reclamo):
        """Permite cancelar un reclamo si está en estado 'Pendiente'."""
        reclamo = self.reclamo_repo.obtener_por_id(id_reclamo)
        if not reclamo:
            return {"error": "Reclamo no encontrado"}, 404

        if reclamo.ESTADO != "Pendiente":
            return {"error": "No puedes cancelar un reclamo en proceso o atendido"}, 400

        reclamo.ESTADO = "Cancelado por el cliente"
        self.reclamo_repo.actualizar(reclamo)

        return {"message": "Reclamo cancelado exitosamente"}, 200

    def actualizar_estado(self, id_reclamo, nuevo_estado):
        """Actualiza el estado de un reclamo."""
        reclamo = self.reclamo_repo.obtener_por_id(id_reclamo)
        if not reclamo:
            return {"error": "Reclamo no encontrado"}, 404

        reclamo.ESTADO = nuevo_estado
        self.reclamo_repo.actualizar(reclamo)

        return {"ID_RECLAMO": reclamo.ID_RECLAMO, "ESTADO": reclamo.ESTADO}, 200

    def obtener_reclamos(self, dni):
        """Obtiene todos los reclamos de un usuario, incluyendo sus datos personales."""
        usuario = self.usuario_repo.obtener_por_dni(dni)
        if not usuario:
            return {"error": "Usuario no encontrado"}, 404

        reclamos = self.reclamo_repo.obtener_por_usuario(usuario.COD_USER)
        if not reclamos:
            return {"message": "No hay reclamos registrados"}, 200

        resultado = []
        for reclamo in reclamos:
            resultado.append({
                "ID_RECLAMO": reclamo.ID_RECLAMO,
                "DESCRIPCION": reclamo.DESCRIPCION,
                "ESTADO": reclamo.ESTADO,
                "FECHA_RECLAMO": reclamo.FECHA_RECLAMO,
                "NOMBRE": usuario.NOMBRE,
                "APELLIDO": usuario.APELLIDO,
                "DNI": usuario.DNI,
                "DIRECCION": usuario.DIRECCION
            })

        return resultado, 200
