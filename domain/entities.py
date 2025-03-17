# domain/entities.py

from flask_sqlalchemy import SQLAlchemy
from datetime import datetime, date

db = SQLAlchemy()

class UsuarioDB1(db.Model):
    """
    Usuario original en DB1 (solo lectura).
    """
    __tablename__ = 'WS_USERS'
    __bind_key__ = 'db1'

    COD_USER = db.Column(db.Integer, primary_key=True)
    DNI = db.Column(db.String(20), nullable=False)
    MAIL = db.Column(db.String(100), nullable=True)
    CELULAR = db.Column(db.String(20), nullable=True)
    FEC_ADD = db.Column(db.Date, nullable=True)
    APELLIDO = db.Column(db.String(50), nullable=True)
    FEC_VALIDACION = db.Column(db.Date, nullable=True)
    NOMBRE = db.Column(db.String(50), nullable=True)
    NUMERO_SUMINISTRO = db.Column(db.String(50), nullable=True)
    NUMERO_MEDIDOR = db.Column(db.String(50), nullable=True)
    DIRECCION = db.Column(db.String(200), nullable=True)

    def to_dict(self):
        return {
            'COD_USER': self.COD_USER,
            'DNI': self.DNI,
            'MAIL': self.MAIL,
            'CELULAR': self.CELULAR,
            'FEC_ADD': self.FEC_ADD.isoformat() if self.FEC_ADD else None,
            'APELLIDO': self.APELLIDO,
            'FEC_VALIDACION': self.FEC_VALIDACION.isoformat() if self.FEC_VALIDACION else None,
            'NOMBRE': self.NOMBRE,
            'NUMERO_SUMINISTRO': self.NUMERO_SUMINISTRO,
            'NUMERO_MEDIDOR': self.NUMERO_MEDIDOR,
            'DIRECCION': self.DIRECCION
        }


class UsuarioDB2(db.Model):
    """
    Usuario copiado en DB2 (lectura/escritura).
    """
    __tablename__ = 'WS_USERS'
    __bind_key__ = 'db2'

    COD_USER = db.Column(db.Integer, primary_key=True)
    DNI = db.Column(db.String(20), nullable=False, unique=True)
    MAIL = db.Column(db.String(100), nullable=True)
    CELULAR = db.Column(db.String(20), nullable=True)
    FEC_ADD = db.Column(db.Date, nullable=True)
    APELLIDO = db.Column(db.String(50), nullable=True)
    FEC_VALIDACION = db.Column(db.Date, nullable=True)
    NOMBRE = db.Column(db.String(50), nullable=True)
    NUMERO_SUMINISTRO = db.Column(db.String(50), nullable=True)
    NUMERO_MEDIDOR = db.Column(db.String(50), nullable=True)
    DIRECCION = db.Column(db.String(200), nullable=True)

    # Relación con Reclamo
    reclamos = db.relationship("Reclamo", back_populates="usuario", lazy="joined")

    def to_dict(self, include_reclamos=False):
        base_dict = {
            'COD_USER': self.COD_USER,
            'DNI': self.DNI,
            'MAIL': self.MAIL,
            'CELULAR': self.CELULAR,
            'FEC_ADD': self.FEC_ADD.isoformat() if self.FEC_ADD else None,
            'APELLIDO': self.APELLIDO,
            'FEC_VALIDACION': self.FEC_VALIDACION.isoformat() if self.FEC_VALIDACION else None,
            'NOMBRE': self.NOMBRE,
            'NUMERO_SUMINISTRO': self.NUMERO_SUMINISTRO,
            'NUMERO_MEDIDOR': self.NUMERO_MEDIDOR,
            'DIRECCION': self.DIRECCION
        }
        if include_reclamos:
            base_dict['reclamos'] = [r.to_dict() for r in self.reclamos] if self.reclamos else []
        return base_dict


class Reclamo(db.Model):
    """
    Reclamo asociado a un usuario en DB2 (lectura/escritura).
    """
    __tablename__ = 'Reclamos'
    __bind_key__ = 'db2'

    ID_RECLAMO = db.Column(db.Integer, primary_key=True)
    COD_USER = db.Column(db.Integer, db.ForeignKey('WS_USERS.COD_USER'), nullable=False)
    DESCRIPCION = db.Column(db.String(500), nullable=False)
    ESTADO = db.Column(db.String(20), default="Pendiente")
    FECHA_RECLAMO = db.Column(db.DateTime, default=datetime.now)
    FECHA_CIERRE = db.Column(db.DateTime, nullable=True)

    # Relación con UsuarioDB2
    usuario = db.relationship("UsuarioDB2", back_populates="reclamos")

    def to_dict(self):
        """
        Combina la información del reclamo y parte del usuario (si lo hay).
        'cliente' será un OBJETO con 'nombre' y 'dni', para que Vue pueda usar:
            cliente.nombre
            cliente.dni
        """
        usuario = self.usuario
        if not usuario:
            # Si no hay usuario, devolvemos algo por defecto
            return {
                'ID_RECLAMO': self.ID_RECLAMO,
                'COD_USER': self.COD_USER,
                'DESCRIPCION': self.DESCRIPCION,
                'ESTADO': self.ESTADO,
                'FECHA_RECLAMO': self.FECHA_RECLAMO.isoformat() if self.FECHA_RECLAMO else None,
                'FECHA_CIERRE': self.FECHA_CIERRE.isoformat() if self.FECHA_CIERRE else None,
                'cliente': {
                    'nombre': "Desconocido",
                    'dni': "Desconocido"
                },
                'numeroSuministro': "Desconocido",
                'medidor': "Desconocido",
                'direccion': "Desconocido"
            }

        # Caso en que SÍ exista usuario
        nombre_completo = f"{usuario.NOMBRE or ''} {usuario.APELLIDO or ''}".strip()

        return {
            'ID_RECLAMO': self.ID_RECLAMO,
            'COD_USER': self.COD_USER,
            'DESCRIPCION': self.DESCRIPCION,
            'ESTADO': self.ESTADO,
            'FECHA_RECLAMO': self.FECHA_RECLAMO.isoformat() if self.FECHA_RECLAMO else None,
            'FECHA_CIERRE': self.FECHA_CIERRE.isoformat() if self.FECHA_CIERRE else None,
            # 🔴 'cliente' es objeto con 'nombre' y 'dni'
            'cliente': {
                'nombre': nombre_completo or "Desconocido",
                'dni': usuario.DNI or "Desconocido"
            },
            'numeroSuministro': usuario.NUMERO_SUMINISTRO or "Desconocido",
            'medidor': usuario.NUMERO_MEDIDOR or "Desconocido",
            'direccion': usuario.DIRECCION or "Desconocido"
        }
