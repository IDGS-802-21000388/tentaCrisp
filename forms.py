from flask_wtf import FlaskForm
from wtforms import StringField, PasswordField
from wtforms.validators import DataRequired, Length
from flask_wtf.recaptcha import RecaptchaField

class UsuarioForm(FlaskForm):
    nombreUsuario = StringField('Usuario', validators=[DataRequired(), Length(min=4, max=100)])
    contrasenia = PasswordField('Contraseña', validators=[DataRequired(), Length(min=6, max=100)])
    #recaptcha = RecaptchaField()
