# infrastructure/users_repository.py
from sqlalchemy.orm import Session
from sqlalchemy.exc import IntegrityError
from domain.entities import Usuario, Rol
from .security import hash_password, verify_password
from datetime import datetime
import logging

logging.basicConfig(level=logging.INFO, format="%(asctime)s - %(levelname)s - %(message)s")

class SQLAlchemyUSERS:
    def __init__(self, session: Session):
        self.session = session

    def create_usuario(self, usuario: str, email: str, password: str, operador_crea: str, roles: list[str] = None):
        logging.info(f"Creando nuevo usuario: {usuario}")
        hashed_password = hash_password(password)
        db_usuario = Usuario(
            Usuario=usuario,
            email=email,
            Pass=hashed_password,
            FechaCrea=datetime.utcnow(),
            OperadorCrea=operador_crea,
            Anulado=False
        )
        if roles:
            db_usuario.roles = self.session.query(Rol).filter(Rol.Nombre.in_(roles)).all()
            if len(db_usuario.roles) != len(roles):
                logging.warning(f"Algunos roles no encontrados: {set(roles) - {r.Nombre for r in db_usuario.roles}}")
        try:
            self.session.add(db_usuario)
            self.session.commit()
            self.session.refresh(db_usuario)
            logging.info(f"Usuario {usuario} creado exitosamente.")
            return db_usuario
        except IntegrityError:
            self.session.rollback()
            logging.error(f"Error: El usuario {usuario} o email {email} ya existe.")
            raise ValueError("El usuario o email ya existe.")

    def get_usuario_by_id(self, id_usuario: int):
        logging.info(f"Buscando usuario por ID: {id_usuario}")
        usuario = self.session.query(Usuario).filter(Usuario.IdUsuario == id_usuario).first()
        return usuario

    def get_usuario_by_username(self, username: str):
        logging.info(f"Buscando usuario por username: {username}")
        usuario = self.session.query(Usuario).filter(Usuario.Usuario == username).first()
        return usuario

    def get_all_usuarios(self):
        logging.info("Obteniendo todos los usuarios")
        usuarios = self.session.query(Usuario).all()
        return usuarios

    def update_usuario(self, id_usuario: int, usuario: str = None, email: str = None, password: str = None, operador_modifica: str = None, roles: list[str] = None):
        logging.info(f"Actualizando usuario con ID: {id_usuario}")
        db_usuario = self.get_usuario_by_id(id_usuario)
        if not db_usuario:
            logging.warning(f"Usuario con ID {id_usuario} no encontrado.")
            return None
        if usuario:
            db_usuario.Usuario = usuario
        if email:
            db_usuario.email = email
        if password:
            db_usuario.Pass = hash_password(password)
        if roles is not None:
            db_usuario.roles = self.session.query(Rol).filter(Rol.Nombre.in_(roles)).all() if roles else []
            if roles and len(db_usuario.roles) != len(roles):
                logging.warning(f"Algunos roles no encontrados: {set(roles) - {r.Nombre for r in db_usuario.roles}}")
        if operador_modifica:
            db_usuario.UsuarioModifica = operador_modifica
            db_usuario.FechaModifica = datetime.utcnow()
        try:
            self.session.commit()
            self.session.refresh(db_usuario)
            logging.info(f"Usuario con ID {id_usuario} actualizado exitosamente.")
            return db_usuario
        except IntegrityError:
            self.session.rollback()
            logging.error(f"Error: El usuario {usuario} o email {email} ya existe.")
            raise ValueError("El usuario o email ya existe.")

    def delete_usuario(self, id_usuario: int, operador_anula: str):
        logging.info(f"Anulando usuario con ID: {id_usuario}")
        db_usuario = self.get_usuario_by_id(id_usuario)
        if not db_usuario:
            logging.warning(f"Usuario con ID {id_usuario} no encontrado.")
            return None
        db_usuario.Anulado = True
        db_usuario.FechaAnula = datetime.utcnow()
        db_usuario.UsuarioAnula = operador_anula
        try:
            self.session.commit()
            self.session.refresh(db_usuario)
            logging.info(f"Usuario con ID {id_usuario} anulado exitosamente.")
            return db_usuario
        except Exception as e:
            self.session.rollback()
            logging.error(f"Error al anular usuario {id_usuario}: {str(e)}")
            raise ValueError("Error al anular usuario.")

    def authenticate_user(self, usuario: str, password: str):
        print("Sesión:", self.session)
        print("Modelo Usuario:", Usuario)
        print("Consulta SQL:", str(self.session.query(Usuario).filter(Usuario.Usuario == usuario)))
        db_usuario = self.session.query(Usuario).filter(Usuario.Usuario == usuario).first()
        if not db_usuario:
            return None
        if not verify_password(password, db_usuario.Pass):
            return None
        return db_usuario