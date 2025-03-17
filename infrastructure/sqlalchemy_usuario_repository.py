# infrastructure/sqlalchemy_usuario_repository.py
from sqlalchemy.orm import Session
from domain.entities import db, UsuarioDB1, UsuarioDB2, Reclamo

class SQLAlchemyUsuarioRepository:
    def __init__(self, session: Session):
        self.session = session

    def obtener_por_dni(self, dni: str):
        """Busca un usuario por DNI en DECSA_DB2."""
        return self.session.query(UsuarioDB2).filter(UsuarioDB2.DNI == dni).first()

    def obtener_de_db1(self, dni: str):
        """Busca un usuario por DNI en DECSA_DB1."""
        return self.session.query(UsuarioDB1).filter_by(DNI=dni).first()

    def existe_en_db2(self, dni: str):
        """Verifica si un usuario ya existe en DECSA_DB2."""
        return self.session.query(UsuarioDB2).filter_by(DNI=dni).first() is not None

    def guardar_en_db2(self, usuario: UsuarioDB2):
        """Guarda un nuevo usuario en DECSA_DB2."""
        self.session.add(usuario)
        self.session.commit()

    def actualizar_usuario(self, dni: str, nuevos_datos: dict):
        """
        Actualiza campos permitidos de un usuario en DB2.
        """
        usuario = self.obtener_por_dni(dni)
        if not usuario:
            return None  # o lanzar excepción

        # Asignar campos
        for campo, valor in nuevos_datos.items():
            setattr(usuario, campo, valor)

        # Guardar cambios
        self.session.commit()
        return usuario
