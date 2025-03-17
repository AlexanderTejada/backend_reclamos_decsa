#application/ actualizar_usuario_usecase.py
from domain.entities import UsuarioDB1, UsuarioDB2
from infrastructure.sqlalchemy_usuario_repository import SQLAlchemyUsuarioRepository

class ActualizarUsuarioUseCase:
    def __init__(self, usuario_repository: SQLAlchemyUsuarioRepository):
        self.usuario_repository = usuario_repository

    def ejecutar(self, dni: str, nuevos_datos: dict):
        """Actualiza los datos de un usuario, copiándolo desde DB1 si no está en DB2."""

        # 🔹 Primero, intentamos obtener al usuario en DB2
        usuario = self.usuario_repository.obtener_por_dni(dni)

        # 🔹 Si no existe en DB2, intentamos copiarlo desde DB1
        if not usuario:
            usuario = self.usuario_repository.copiar_usuario_a_db2(dni)
            if not usuario:
                return {"error": "Usuario no encontrado en ninguna base de datos"}, 404

        # 🔹 Filtrar los datos para evitar actualizaciones no permitidas
        campos_permitidos = ["MAIL", "CELULAR", "DIRECCION"]
        datos_filtrados = {k: v for k, v in nuevos_datos.items() if k in campos_permitidos}

        if not datos_filtrados:
            return {"error": "No se enviaron datos válidos para actualizar"}, 400

        # 🔹 Actualizar usuario en la base de datos
        usuario_actualizado = self.usuario_repository.actualizar_usuario(dni, datos_filtrados)

        return usuario_actualizado.to_dict(), 200
