# infraestructure/SQLAlchemyReclamoRepository.py
from sqlalchemy.orm import Session, joinedload
from domain.entities import Reclamo, Cliente
from datetime import datetime
import logging

logging.basicConfig(level=logging.INFO, format="%(asctime)s - %(levelname)s - %(message)s")

class SQLAlchemyReclamoRepository:
    def __init__(self, session: Session):
        self.session = session

    def obtener_por_id(self, id_reclamo: int):
        return (
            self.session.query(Reclamo)
            .options(joinedload(Reclamo.cliente))
            .filter(Reclamo.ID_RECLAMO == id_reclamo)
            .first()
        )

    def obtener_por_usuario(self, id_usuario: int):
        return (
            self.session.query(Reclamo)
            .filter(Reclamo.ID_USUARIO == id_usuario)
            .all()
        )

    def guardar(self, reclamo: Reclamo):
        try:
            self.session.add(reclamo)
            self.session.commit()
            logging.info(f"Reclamo guardado correctamente con ID {reclamo.ID_RECLAMO}")
            return reclamo
        except Exception as e:
            self.session.rollback()
            logging.error(f"Error al guardar reclamo: {str(e)}")
            raise

    def actualizar_estado(self, id_reclamo: int, nuevo_estado: str):
        try:
            reclamo = self.obtener_por_id(id_reclamo)
            if reclamo:
                reclamo.ESTADO = nuevo_estado
                # Si el estado es "Resuelto", actualizamos FECHA_CIERRE
                if nuevo_estado == "Resuelto":
                    reclamo.FECHA_CIERRE = datetime.now()
                # Si el estado cambia de "Resuelto" a otro, limpiamos FECHA_CIERRE
                elif reclamo.FECHA_CIERRE and nuevo_estado != "Resuelto":
                    reclamo.FECHA_CIERRE = None
                self.session.commit()
                logging.info(f"Estado del reclamo {id_reclamo} actualizado a {nuevo_estado}")
                return reclamo
            logging.warning(f"Reclamo con ID {id_reclamo} no encontrado para actualizar estado.")
            return None
        except Exception as e:
            self.session.rollback()
            logging.error(f"Error al actualizar estado del reclamo {id_reclamo}: {str(e)}")
            raise

    def listar_todos(self):
        return (
            self.session.query(Reclamo)
            .options(joinedload(Reclamo.cliente))
            .all()
        )

    def listar_pendientes(self):
        return (
            self.session.query(Reclamo)
            .options(joinedload(Reclamo.cliente))
            .filter(Reclamo.ESTADO == "Pendiente")
            .all()
        )