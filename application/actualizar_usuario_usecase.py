#actualizar_usuario_usecase.py
import logging
from domain.entities import Cliente
from infrastructure.sqlalchemy_usuario_repository import SQLAlchemyUsuarioRepository

logging.basicConfig(level=logging.INFO, format="%(asctime)s - %(levelname)s - %(message)s")

class ActualizarUsuarioUseCase:
    def __init__(self, usuario_repository: SQLAlchemyUsuarioRepository):
        self.usuario_repository = usuario_repository

    def ejecutar(self, dni: str, nuevos_datos: dict):
        """Actualiza los datos de un cliente, copiándolo desde DB1 si no está en DB2."""
        cliente = self.usuario_repository.obtener_por_dni(dni)
        if not cliente:
            cliente = self.usuario_repository.copiar_cliente_a_db2(dni)
            if not cliente:
                logging.error(f"Cliente no encontrado en ninguna base de datos para DNI {dni}")
                return {"error": "Cliente no encontrado en ninguna base de datos"}, 404

        # Campos que se pueden actualizar
        campos_permitidos = ["EMAIL", "CELULAR", "CALLE", "BARRIO"]
        datos_filtrados = {k: v for k, v in nuevos_datos.items() if k in campos_permitidos}

        if not datos_filtrados and nuevos_datos:
            logging.warning(f"No se enviaron datos válidos para actualizar para DNI {dni}")
            return {"error": "No se enviaron datos válidos para actualizar"}, 400

        if not datos_filtrados:
            logging.info(f"No hay datos para actualizar para DNI {dni}, devolviendo datos actuales")
            return cliente.to_dict(), 200

        # Actualizar cada campo permitido
        for campo, valor in datos_filtrados.items():
            setattr(cliente, campo, valor)

        self.usuario_repository.actualizar_cliente(cliente)
        logging.info(f"Cliente actualizado exitosamente para DNI {dni}")
        return cliente.to_dict(), 200