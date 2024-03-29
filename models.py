from flask_sqlalchemy import SQLAlchemy
from datetime import datetime
from flask_login import UserMixin
from sqlalchemy.dialects.mysql import LONGTEXT

db = SQLAlchemy()

class Usuario(db.Model, UserMixin):
    idUsuario = db.Column(db.Integer, primary_key=True, autoincrement=True)
    nombre=db.Column(db.String(45), nullable=False, default=None)
    nombreUsuario = db.Column(db.String(45), nullable=False, default="")
    contrasenia = db.Column(db.String(200), nullable=False, default="")
    rol = db.Column(db.String(30), nullable=False)
    estatus = db.Column(db.Integer, nullable=False, default=1)
    telefono = db.Column(db.String(15), nullable=False, default="")
    dateLastToken = db.Column(db.DateTime, nullable=True, default=datetime.utcnow)
    def is_active(self):
        return self.estatus != 0
    def get_id(self):
        return str(self.idUsuario) 

class LogsUser(db.Model):
    id = db.Column(db.Integer, primary_key=True, autoincrement=True)
    procedimiento = db.Column(db.String(255), nullable=False)
    lastDate = db.Column(db.DateTime, nullable=True, default=datetime.utcnow)
    idUsuario = db.Column(db.Integer)

class Medida(db.Model):
    idMedida = db.Column(db.Integer, primary_key=True, autoincrement=True)
    tipoMedida = db.Column(db.String(15))

class Proveedor(db.Model):
    idProveedor = db.Column(db.Integer, primary_key=True, autoincrement=True)
    nombreProveedor = db.Column(db.String(100), nullable=False, default="")
    direccion = db.Column(db.String(255), nullable=False, default="")
    telefono = db.Column(db.String(15), nullable=False, default="")
    nombreAtiende = db.Column(db.String(100), nullable=False, default="")
    estatus = db.Column(db.Integer, nullable=False, default=1)

    # Relación con la tabla MateriaPrima
    materia_prima = db.relationship('MateriaPrima', backref='proveedor', lazy=True)

class MateriaPrima(db.Model):
    idMateriaPrima = db.Column(db.Integer, primary_key=True, autoincrement=True)
    nombreMateria = db.Column(db.String(45), nullable=False, default="")
    estatus = db.Column(db.Integer, nullable=False, default=1)
    precioCompra = db.Column(db.Float, nullable=False, default=0.0)
    porcentaje = db.Column(db.Integer, nullable=False, default=100)
    idMedida = db.Column(db.Integer, db.ForeignKey('medida.idMedida'))
    idProveedor = db.Column(db.Integer, db.ForeignKey('proveedor.idProveedor'))

class Detalle_materia_prima(db.Model):
    idDetalle_materia_prima = db.Column(db.Integer, primary_key=True, autoincrement=True)
    fechaCompra = db.Column(db.DateTime, nullable=False, default=datetime.utcnow)
    fechaVencimiento = db.Column(db.DateTime)
    cantidadExistentes = db.Column(db.Float, nullable=False, default=0.0)
    estatus = db.Column(db.Integer, nullable=False, default=1)
    idMateriaPrima = db.Column(db.Integer, db.ForeignKey('materia_prima.idMateriaPrima'))

class Producto(db.Model):
    idProducto = db.Column(db.Integer, primary_key=True, autoincrement=True)
    nombreProducto = db.Column(db.String(50), nullable=False, default="")
    precioVenta = db.Column(db.Float, nullable=False, default=0.0)
    precioProduccion = db.Column(db.Float, nullable=False, default=0.0)
    idMedida = db.Column(db.Integer, db.ForeignKey('medida.idMedida'))
    fotografia = db.Column(LONGTEXT)
    estatus = db.Column(db.Boolean, nullable=False, default=True)
    
    # Relación con la tabla Medida
    medida = db.relationship('Medida', backref='productos', lazy=True)

class Detalle_producto(db.Model):
    idDetalle_producto = db.Column(db.Integer, primary_key=True, autoincrement=True)
    fechaVencimiento = db.Column(db.DateTime)
    cantidadExistentes = db.Column(db.Integer, nullable=False, default=0.0)
    estatus = db.Column(db.Boolean, nullable=False, default=True)

    idProducto = db.Column(db.Integer, db.ForeignKey('producto.idProducto'))

class merma(db.Model):
    idMerma = db.Column(db.Integer, primary_key=True, autoincrement=True)
    cantidadMerma= db.Column(db.Float, nullable=False, default=0.0)
    idProducto = db.Column(db.Integer, db.ForeignKey('producto.idProducto'))
    idMateriaPrima = db.Column(db.Integer, db.ForeignKey('materia_prima.idMateriaPrima'))

class Receta(db.Model):
    idReceta = db.Column(db.Integer, primary_key=True, autoincrement=True)
    idMedida = db.Column(db.Integer, db.ForeignKey('medida.idMedida'))
    idProducto = db.Column(db.Integer, db.ForeignKey('producto.idProducto'))
     # Relación con la tabla Medida
    medida = db.relationship('Medida', backref='receta', lazy=True)

class Detalle_receta(db.Model):
    idDetalle_receta = db.Column(db.Integer, primary_key=True, autoincrement=True)
    porcion = db.Column(db.Float, nullable=False, default=0.0)
    idMateriaPrima = db.Column(db.Integer, db.ForeignKey('materia_prima.idMateriaPrima'))
    idReceta = db.Column(db.Integer, db.ForeignKey('receta.idReceta'))

    # Relación con la tabla Producto
    # producto = db.relationship('Producto', backref='receta', lazy=True)
    # Relación con la tabla MateriaPrima
    materia_prima = db.relationship('MateriaPrima', backref='receta', lazy=True)

class Venta(db.Model):
    idVenta = db.Column(db.Integer, primary_key=True, autoincrement=True)
    fechaVenta = db.Column(db.DateTime, nullable=False, default=datetime.utcnow)
    total = db.Column(db.Float, nullable=False, default=0.0)

class DetalleVenta(db.Model):
    idDetalleVenta = db.Column(db.Integer, primary_key=True, autoincrement=True)
    cantidad = db.Column(db.Float, nullable=False, default=0.0)
    subtotal = db.Column(db.Float, nullable=False, default=0.0)
    idVenta = db.Column(db.Integer, db.ForeignKey('venta.idVenta'))
    idProducto = db.Column(db.Integer, db.ForeignKey('producto.idProducto'))
    idMedida = db.Column(db.Integer, db.ForeignKey('medida.idMedida'))

class Movimiento(db.Model):
    idMovimiento = db.Column(db.Integer, primary_key=True, autoincrement=True)
    fechaMovimiento = db.Column(db.DateTime, nullable=False, default=datetime.utcnow)
    tipoMovimiento = db.Column(db.String(45), nullable=False, default="")
    monto = db.Column(db.Float, nullable=False, default=0.0)
    idVenta = db.Column(db.Integer, db.ForeignKey('venta.idVenta'))
    idMateriaPrima = db.Column(db.Integer, db.ForeignKey('materia_prima.idMateriaPrima'))
