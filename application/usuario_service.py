#apllication/usuario_service.py
import logging
from domain.entities import UsuarioDB1, UsuarioDB2
from infrastructure.sqlalchemy_usuario_repository import SQLAlchemyUsuarioRepository


class UsuarioService:
    def __init__(self, usuario_repo: SQLAlchemyUsuarioRepository):
        self.usuario_repo = usuario_repo

    def obtener_usuario_por_dni(self, dni):
        """Obtiene un usuario por su DNI en DECSA_DB2. Si no existe, lo copia desde DECSA_DB1."""
        logging.info(f"Buscando usuario con DNI: {dni}")

        usuario = self.usuario_repo.obtener_por_dni(dni)

        # 🔹 Si el usuario no está en DB2, intentamos copiarlo desde DB1
        if not usuario:
            logging.warning(f"Usuario con DNI {dni} no encontrado en DECSA_DB2. Buscando en DECSA_DB1...")
            usuario = self.copiar_usuario_a_db2(dni)  # 🔹 Intentamos copiar desde DB1

            if isinstance(usuario, tuple):  # Si devuelve error (dict, 404), extraemos solo la data
                usuario = usuario[0] if usuario[1] == 201 else None

            if not usuario:
                logging.error(f"Usuario con DNI {dni} no encontrado en ninguna base de datos.")
                return {"error": "Usuario no encontrado"}, 404

        logging.info(f"Usuario encontrado: {usuario['NOMBRE']} {usuario['APELLIDO']}")
        return usuario, 200

    def copiar_usuario_a_db2(self, dni):
        """Copia un usuario desde DECSA_DB1 a DECSA_DB2 si no existe."""
        logging.info(f"Intentando copiar usuario con DNI: {dni}")

        usuario_original = self.usuario_repo.obtener_de_db1(dni)
        if not usuario_original:
            logging.error(f"Usuario con DNI {dni} no encontrado en DECSA_DB1")
            return {"error": "Usuario no encontrado en DECSA_DB1"}, 404

        if self.usuario_repo.existe_en_db2(dni):
            logging.warning(f"El usuario con DNI {dni} ya existe en DECSA_DB2")
            return {"error": "El usuario ya existe en DECSA_DB2"}, 409

        nuevo_usuario = UsuarioDB2(
            COD_USER=usuario_original.COD_USER,
            DNI=usuario_original.DNI,
            MAIL=usuario_original.MAIL,
            CELULAR=usuario_original.CELULAR,
            FEC_ADD=usuario_original.FEC_ADD,
            APELLIDO=usuario_original.APELLIDO,
            FEC_VALIDACION=usuario_original.FEC_VALIDACION,
            NOMBRE=usuario_original.NOMBRE,
            NUMERO_SUMINISTRO=usuario_original.NUMERO_SUMINISTRO,
            NUMERO_MEDIDOR=usuario_original.NUMERO_MEDIDOR,
            DIRECCION=usuario_original.DIRECCION,
        )

        self.usuario_repo.guardar_en_db2(nuevo_usuario)
        logging.info(f"Usuario con DNI {dni} copiado exitosamente a DECSA_DB2")
        return nuevo_usuario.to_dict(), 201

    def actualizar_usuario(self, dni, data):
        """Actualiza los datos de un usuario en DECSA_DB2. Si no existe, primero lo copia desde DECSA_DB1."""
        logging.info(f"Intentando actualizar usuario con DNI: {dni}")

        usuario = self.usuario_repo.obtener_por_dni(dni)

        # 🔹 Si no está en DB2, lo copiamos desde DB1
        if not usuario:
            logging.warning(f"Usuario con DNI {dni} no está en DECSA_DB2. Intentando copiar desde DECSA_DB1...")
            usuario = self.copiar_usuario_a_db2(dni)

            if isinstance(usuario, tuple):  # Si devuelve error (dict, 404), extraemos solo la data
                usuario = usuario[0] if usuario[1] == 201 else None

            if not usuario:
                logging.error(f"No se pudo copiar el usuario con DNI {dni} desde DECSA_DB1.")
                return {"error": "Usuario no encontrado"}, 404

        # 🔹 Ahora sí podemos actualizarlo en DB2
        campos_permitidos = ["DIRECCION", "CELULAR", "MAIL"]
        for campo in campos_permitidos:
            if campo in data:
                setattr(usuario, campo, data[campo])

        self.usuario_repo.actualizar(usuario)
        logging.info(f"Usuario con DNI {dni} actualizado exitosamente")
        return usuario.to_dict(), 200
