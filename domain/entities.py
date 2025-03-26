#domain/enteties.py
from flask_sqlalchemy import SQLAlchemy
from datetime import datetime

db = SQLAlchemy()

class Cliente(db.Model):
    __tablename__ = 'Clientes'
    __bind_key__ = 'db2'

    ID_USUARIO = db.Column(db.Integer, primary_key=True)
    DNI = db.Column(db.String(20), nullable=False, unique=True)
    NOMBRE_COMPLETO = db.Column(db.String(150), nullable=False)
    SEXO = db.Column(db.String(1), nullable=True)
    CELULAR = db.Column(db.String(20), nullable=True)
    EMAIL = db.Column(db.String(100), nullable=True)
    CODIGO_POSTAL = db.Column(db.String(10), nullable=True)
    FECHA_ALTA = db.Column(db.Date, nullable=True)
    OBSERVACIONES = db.Column(db.String(500), nullable=True)
    CODIGO_SUMINISTRO = db.Column(db.String(50), nullable=False)
    NUMERO_MEDIDOR = db.Column(db.String(50), nullable=False)
    CALLE = db.Column(db.String(200), nullable=True)
    BARRIO = db.Column(db.String(200), nullable=True)

    reclamos = db.relationship("Reclamo", back_populates="cliente", lazy="joined")

    def to_dict(self, include_reclamos=False):
        data = {
            'ID_USUARIO': self.ID_USUARIO,
            'DNI': self.DNI,
            'NOMBRE_COMPLETO': self.NOMBRE_COMPLETO,
            'SEXO': self.SEXO,
            'CELULAR': self.CELULAR,
            'EMAIL': self.EMAIL,
            'CODIGO_POSTAL': self.CODIGO_POSTAL,
            'FECHA_ALTA': self.FECHA_ALTA.isoformat() if self.FECHA_ALTA else None,
            'OBSERVACIONES': self.OBSERVACIONES,
            'CODIGO_SUMINISTRO': self.CODIGO_SUMINISTRO,
            'NUMERO_MEDIDOR': self.NUMERO_MEDIDOR,
            'CALLE': self.CALLE,
            'BARRIO': self.BARRIO
        }
        if include_reclamos:
            data['reclamos'] = [r.to_dict() for r in self.reclamos]
        return data


class Reclamo(db.Model):
    __tablename__ = 'Reclamos'
    __bind_key__ = 'db2'

    ID_RECLAMO = db.Column(db.Integer, primary_key=True)
    ID_USUARIO = db.Column(db.Integer, db.ForeignKey('Clientes.ID_USUARIO'), nullable=False)
    DESCRIPCION = db.Column(db.String(500), nullable=False)
    ESTADO = db.Column(db.String(20), default="Pendiente")
    FECHA_RECLAMO = db.Column(db.DateTime, default=datetime.now)
    FECHA_CIERRE = db.Column(db.DateTime, nullable=True)

    cliente = db.relationship("Cliente", back_populates="reclamos")

    def to_dict(self):
        return {
            'ID_RECLAMO': self.ID_RECLAMO,
            'ID_USUARIO': self.ID_USUARIO,
            'DESCRIPCION': self.DESCRIPCION,
            'ESTADO': self.ESTADO,
            'FECHA_RECLAMO': self.FECHA_RECLAMO.isoformat() if self.FECHA_RECLAMO else None,
            'FECHA_CIERRE': self.FECHA_CIERRE.isoformat() if self.FECHA_CIERRE else None,
            'cliente': {
                'nombre': self.cliente.NOMBRE_COMPLETO if self.cliente else "Desconocido",
                'dni': self.cliente.DNI if self.cliente else "Desconocido",
                'celular': self.cliente.CELULAR if self.cliente else "N/A",  # Agregado
                'email': self.cliente.EMAIL if self.cliente else "N/A"  # Agregado
            },
            'calle': self.cliente.CALLE if self.cliente else "Sin calle",
            'barrio': self.cliente.BARRIO if self.cliente else "Sin barrio",
            'codigo_postal': self.cliente.CODIGO_POSTAL if self.cliente else "N/A",
            'numeroSuministro': self.cliente.CODIGO_SUMINISTRO if self.cliente else "N/A",
            'medidor': self.cliente.NUMERO_MEDIDOR if self.cliente else "N/A",
        }