# infrastructure/sqlalchemy_reclamo_repository.py
from sqlalchemy.orm import Session, joinedload
from domain.entities import db, UsuarioDB1, UsuarioDB2, Reclamo
from sqlalchemy.orm import joinedload

class SQLAlchemyReclamoRepository:
    def __init__(self, session):
        self.session = session

    def obtener_por_id(self, id_reclamo: int):
        return (
            self.session.query(Reclamo)
            .options(joinedload(Reclamo.usuario))
            .filter(Reclamo.ID_RECLAMO == id_reclamo)
            .first()
        )

    def obtener_por_usuario(self, cod_user: int):
        return (
            self.session.query(Reclamo)
            .filter(Reclamo.COD_USER == cod_user)
            .all()
        )

    def guardar(self, reclamo: Reclamo):
        self.session.add(reclamo)
        self.session.commit()
        return reclamo

    def actualizar_estado(self, id_reclamo: int, nuevo_estado: str):
        reclamo = self.obtener_por_id(id_reclamo)
        if reclamo:
            reclamo.ESTADO = nuevo_estado
            self.session.commit()
            return reclamo
        return None

    def listar_todos(self):
        """
        Retorna TODOS los reclamos, con su relación de usuario ya 'joinloadeada'.
        """
        # joinedload(Reclamo.usuario) se asegura de traer los datos de usuario en una sola consulta
        return (self.session.query(Reclamo)
                .options(joinedload(Reclamo.usuario))
                .all())
