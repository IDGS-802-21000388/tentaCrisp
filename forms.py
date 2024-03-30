from flask_wtf import FlaskForm
from wtforms import Form
from wtforms import StringField, PasswordField
from wtforms.validators import DataRequired, Length, InputRequired
from wtforms import validators ,DateField, SelectField, DecimalField, FileField


class LoginForm(FlaskForm):
    nombreUsuario = StringField('Usuario', validators=[DataRequired(), Length(min=4, max=100)])
    contrasenia = PasswordField('Contraseña', validators=[DataRequired(), Length(min=6, max=100)])

class UsuarioForm(FlaskForm):
    nombre = StringField('Nombre', validators=[DataRequired(), Length(min=4, max=100)])
    nombreUsuario = StringField('Nombre de Usuario', validators=[DataRequired(), Length(min=4, max=100)])
    contrasenia = PasswordField('Contraseña', validators=[DataRequired(), Length(min=6, max=100)])
    rol = SelectField('Rol', choices=[('Administrador', 'Administrador'), ('Gerente', 'Gerente'), ('Produccion', 'Produccion'), ('Venta', 'Venta')])
    telefono=StringField('Telefono',[
        validators.length(min=1,max=11,message='valor no válido')
    ])
class InventarioForm(Form):
    nombre = StringField('Nombre',[validators.DataRequired(message='Favor de ingresar el nombre'),validators.length(min=1,max=40,message='Ingresa nombre valido')])
    precio = StringField('Precio Compra',[validators.DataRequired(message='Favor de ingresar el Precio'),validators.length(min=1,max=40,message='Ingresa nombre valido')])
    cantidad = StringField('Cantidad',[validators.DataRequired(message='Favor de ingresar la cantidad'),validators.length(min=1,max=40,message='Ingresa cantidad valida')])
    fechaVen = DateField('Fecha de Vencimiento', validators=[validators.DataRequired()])
    tipo_compra = SelectField('Tipo de compra', choices=[('bulto', 'Bulto'), ('caja', 'Caja'), ('paquete', 'Paquete'), ('unidad', 'Unidad')])

class ProveedorForm(Form):
    nombreProveedor = StringField('Nombre Proveedor', validators=[DataRequired(), Length(max=100)])
    direccion = StringField('Dirección', validators=[DataRequired(), Length(max=255)])
    telefono = StringField('Teléfono', validators=[DataRequired(), Length(max=15)])
    nombreAtiende = StringField('Repartidor', validators=[DataRequired(), Length(max=100)])
    
class NuevaGalletaForm(FlaskForm):
    nombre_galleta = StringField('Nombre de la galleta', validators=[DataRequired(message='Favor de ingresar el nombre'), Length(min=1, max=40, message='Ingresa un nombre válido')])
    precio_produccion = DecimalField('Precio de producción', validators=[DataRequired(message='Favor de ingresar el precio de producción')])
    precio_venta = DecimalField('Precio de venta', validators=[DataRequired(message='Favor de ingresar el precio de venta')])
    fotografia = FileField('Fotografía')
    fechaCaducidad = DateField('Fecha de Caducidad', validators=[validators.DataRequired()])

class MermaForm(FlaskForm):
    cantidadKilos = DecimalField('Cantidad', validators=[DataRequired()])
