from flask_wtf import FlaskForm
from wtforms import Form
from wtforms import StringField, PasswordField
from wtforms.validators import DataRequired, Length
from flask_wtf.recaptcha import RecaptchaField
from wtforms import validators ,DateField, SelectField

class UsuarioForm(FlaskForm):
    nombreUsuario = StringField('Usuario', validators=[DataRequired(), Length(min=4, max=100)])
    contrasenia = PasswordField('Contraseña', validators=[DataRequired(), Length(min=6, max=100)])
    #recaptcha = RecaptchaField()

class InventarioForm(Form):
    
    nombre = StringField('Nombre',[validators.DataRequired(message='Favor de ingresar el nombre'),
                                   validators.length(min=1,max=40,message='Ingresa nombre valido')
                                   ])
    precio = StringField('Precio Compra',[validators.DataRequired(message='Favor de ingresar el Precio'),
                                   validators.length(min=1,max=40,message='Ingresa nombre valido')
                                   ])
    cantidad = StringField('Cantidad',[validators.DataRequired(message='Favor de ingresar la cantidad'),
                                   validators.length(min=1,max=40,message='Ingresa cantidad valida')
                                   ])
    fechaVen = DateField('Fecha de Vencimiento', validators=[validators.DataRequired()])
    fechaCom = DateField('Fecha de Compra', validators=[validators.DataRequired()])
    tipo_compra = SelectField('Tipo de compra', choices=[('bulto', 'Bulto'), ('caja', 'Caja'), ('paquete', 'Paquete'), ('unidad', 'Unidad')])
    forma_compra = SelectField('Forma de compra', choices=[('Proveedor', 'Proveedor'), ('Manual', 'Manual')])

class ProveedorForm(Form):
    nombreProveedor = StringField('Nombre Proveedor', validators=[DataRequired(), Length(max=100)])
    direccion = StringField('Dirección', validators=[DataRequired(), Length(max=255)])
    telefono = StringField('Teléfono', validators=[DataRequired(), Length(max=15)])
    nombreAtiende = StringField('Nombre del encargado', validators=[DataRequired(), Length(max=100)])
