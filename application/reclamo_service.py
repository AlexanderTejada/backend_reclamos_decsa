import logging
from domain.entities import Cliente, Reclamo
from infrastructure.sqlalchemy_reclamo_repository import SQLAlchemyReclamoRepository
from infrastructure.sqlalchemy_usuario_repository import SQLAlchemyUsuarioRepository

class ReclamoService:
    def __init__(self, reclamo_repo: SQLAlchemyReclamoRepository, usuario_repo: SQLAlchemyUsuarioRepository):
        self.reclamo_repo = reclamo_repo
        self.usuario_repo = usuario_repo

    def crear_reclamo(self, dni, descripcion):
        """Crea un reclamo. Si el cliente no existe en DB2, lo copia desde PR_CAU."""
        logging.info(f"Intentando crear reclamo para DNI: {dni}")

        cliente = self.usuario_repo.obtener_por_dni(dni)

        if not cliente:
            logging.warning(f"Cliente con DNI {dni} no encontrado en DECSA_EXC. Copiando desde PR_CAU...")
            cliente = self.usuario_repo.copiar_cliente_a_db2(dni)
            if not cliente:
                logging.error(f"Cliente con DNI {dni} no encontrado en PR_CAU")
                return {"error": "Cliente no encontrado"}, 404

            # También copiamos las facturas del cliente
            self.usuario_repo.guardar_facturas_en_db2(dni)

        nuevo_reclamo = Reclamo(
            ID_USUARIO=cliente.ID_USUARIO,
            Descripcion=descripcion,
            Estado="Pendiente"
        )

        self.reclamo_repo.guardar(nuevo_reclamo)
        logging.info(f"Reclamo creado exitosamente para cliente {cliente.Nombre}")

        return {
            "ID_RECLAMO": nuevo_reclamo.ID_RECLAMO,
            "Descripcion": nuevo_reclamo.Descripcion,
            "Estado": nuevo_reclamo.Estado,
            "FechaReclamo": nuevo_reclamo.FechaReclamo,
            "Nombre": cliente.Nombre,
            "DNI": cliente.DNI,
            "Direccion": cliente.NombreCalle
        }, 201

    def cancelar_reclamo(self, id_reclamo):
        """Permite cancelar un reclamo si está en estado 'Pendiente'."""
        reclamo = self.reclamo_repo.obtener_por_id(id_reclamo)
        if not reclamo:
            return {"error": "Reclamo no encontrado"}, 404

        if reclamo.Estado != "Pendiente":
            return {"error": "No puedes cancelar un reclamo que ya está en proceso o cerrado"}, 400

        reclamo.Estado = "Cancelado por el cliente"
        self.reclamo_repo.actualizar(reclamo)

        return {"message": "Reclamo cancelado exitosamente"}, 200

    def actualizar_estado(self, id_reclamo, nuevo_estado):
        """Actualiza el estado de un reclamo."""
        reclamo = self.reclamo_repo.obtener_por_id(id_reclamo)
        if not reclamo:
            return {"error": "Reclamo no encontrado"}, 404

        reclamo.Estado = nuevo_estado
        self.reclamo_repo.actualizar(reclamo)

        return {"ID_RECLAMO": reclamo.ID_RECLAMO, "Estado": reclamo.Estado}, 200

    def obtener_reclamos(self, dni):
        """Obtiene todos los reclamos de un cliente por DNI."""
        cliente = self.usuario_repo.obtener_por_dni(dni)
        if not cliente:
            return {"error": "Cliente no encontrado"}, 404

        reclamos = self.reclamo_repo.obtener_por_usuario(cliente.ID_USUARIO)
        if not reclamos:
            return {"message": "No hay reclamos registrados"}, 200

        resultado = []
        for reclamo in reclamos:
            resultado.append({
                "ID_RECLAMO": reclamo.ID_RECLAMO,
                "Descripcion": reclamo.Descripcion,
                "Estado": reclamo.Estado,
                "FechaReclamo": reclamo.FechaReclamo,
                "Nombre": cliente.Nombre,
                "DNI": cliente.DNI,
                "Direccion": cliente.NombreCalle
            })

        return resultado, 200
