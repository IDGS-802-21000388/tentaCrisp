from flask import Flask, request, render_template, flash, g, redirect, url_for, session, jsonify
from flask_wtf.csrf import CSRFProtect
from config import DevelopmentConfig
import forms, ssl, re
from models import db, Usuario, MateriaPrima
from sqlalchemy import func
from functools import wraps
from flask_cors import CORS
from flask_wtf.recaptcha import Recaptcha
from datetime import datetime
from flask_login import LoginManager, login_user, logout_user, login_required, login_manager
from werkzeug.security import generate_password_hash, check_password_hash
from sqlalchemy.orm import Session
ssl._create_default_https_context = ssl._create_unverified_context


app = Flask(__name__)
app.config.from_object(DevelopmentConfig)
csrf = CSRFProtect()
CORS(app, resources={r"/*": {"origins": app.config['CORS_ORIGINS']}})
login_manager = LoginManager()
login_manager.init_app(app)
#login_manager.login_view = 'login'
# recaptcha = Recaptcha(app)

@login_manager.user_loader
def load_user(user_id):
    return Usuario.query.get(int(user_id))

@app.errorhandler(404)
def page_not_found(e):
    return render_template("404.html"),404

@login_manager.unauthorized_handler
def unauthorized():
    #flash('Por favor, inicia sesión para acceder a esta página.', 'warning')
    return redirect(url_for('login'))

@app.route('/', methods=['GET', 'POST'])
def login():
    usuario_form = forms.LoginForm(request.form)
    
    if request.method == 'POST' and usuario_form.validate():
        print(request.form)
        nombreUsuario = usuario_form.nombreUsuario.data
        contrasenia = usuario_form.contrasenia.data
        user = Usuario.query.filter_by(nombreUsuario=nombreUsuario).first()
        print("Contraseña",generate_password_hash(contrasenia))
        if user and check_password_hash(user.contrasenia, contrasenia):
            
            login_user(user)
            #flash('Inicio de sesión exitoso', 'success')
            user.dateLastToken = datetime.utcnow()
            db.session.commit()
            return jsonify({'success': True, 'redirect': url_for('index')})
        else:
            #flash('Usuario o contraseña inválidos', 'error')
            return jsonify({'success': False, 'error': 'Usuario o contraseña inválidos'})
    
    return render_template('login.html', form=usuario_form)

@app.route('/logout', methods=['POST'])
@login_required
def logout():
    logout_user()
    return redirect(url_for('login'))

@app.route('/index')
@login_required
def index():
    return render_template('index.html')

@app.route("/inventario")
def inventario():
    nombre = ""
    precio = ""
    cantidad = ""
    tipo_compra = ""
    fechaVen = ""
    fechaCom = ""
    forma_compra = ""
    inventario = forms.InventarioForm(request.form)
    if request.method == 'POST' and inventario.validate():
        nombre = inventario.nombre.data
        precio = inventario.precio.data
        cantidad = inventario.cantidad.data
        tipo_compra = request.form.get('tipo_compra')
        fechaVen = inventario.fechaVen.data
        fechaCom = inventario.fechaCom.data
        forma_compra = request.form.get('forma_compra')

    datos_materia_prima = MateriaPrima.query.all()
    materia_prima_json = []
    for materia in datos_materia_prima:
        materia_prima_json.append({
            'nombre': materia.nombreMateria,
            'cantidad': materia.cantidadExistentes,
            'tipo': materia.medida.tipoMedida,
            'precio_compra': materia.precioCompra,
            'fecha_compra': materia.fechaCompra.strftime('%Y-%m-%d'),
            'fecha_vencimiento': materia.fechaVencimiento.strftime('%Y-%m-%d') if materia.fechaVencimiento else None,
            'porcentaje': materia.porcentaje
        })

    return render_template("vista_Inventario.html", form=inventario, datos_materia_prima=materia_prima_json, nombre=nombre, precio=precio, cantidad=cantidad, tipo_compra=tipo_compra, fechaVen=fechaVen, fechaCom=fechaCom, forma_compra=forma_compra)

@app.route('/recetas')
def recetas():
    return render_template('receta.html')

password_pattern = re.compile(r'^(?=.*[a-z])(?=.*[A-Z])(?=.*\d)(?=.*[@$!%*?&])[A-Za-z\d@$!%*?&]{8,}$')

@app.route('/usuarios', methods=['GET', 'POST'])
def usuarios():
    usuario_form = forms.UsuarioForm(request.form)
    if request.method == 'POST' and usuario_form.validate():
        nombre = usuario_form.nombre.data
        nombreUsuario = usuario_form.nombreUsuario.data
        contrasenia = usuario_form.contrasenia.data
        rol = usuario_form.rol.data
        telefono = usuario_form.telefono.data
        
         # Verificar si la contraseña no está en la lista de contraseñas por defecto o previamente utilizadas
        if contrasenia in lista_contraseñas_no_seguras:
            flash('La contraseña no puede ser una contraseña por defecto o previamente utilizada.', 'error')
            return redirect(url_for('usuarios'))
        
        # Verificar si la contraseña cumple con la política de seguridad
        if not password_pattern.match(contrasenia):
            flash('La contraseña debe contener al menos una mayúscula, una minúscula, un número y un carácter especial.', 'error')
            return redirect(url_for('usuarios'))

        # Verificar si la contraseña no está en la lista de contraseñas por defecto o previamente utilizadas
        if contrasenia in lista_contraseñas_no_seguras:
            flash('La contraseña no puede ser una contraseña por defecto o previamente utilizada.', 'error')
            return redirect(url_for('usuarios'))

        # Hash de la contraseña antes de guardarla
        contrasenia_hash = generate_password_hash(contrasenia)
        
        nuevo_usuario = Usuario(nombre=nombre, nombreUsuario=nombreUsuario, contrasenia=contrasenia_hash, rol=rol, telefono=telefono)
        db.session.add(nuevo_usuario)
        db.session.commit()
        
        flash('Usuario guardado correctamente', 'success')  
        return redirect(url_for('usuarios'))
    
    usuarios = Usuario.query.all()
        
    return render_template('usuarios.html', form=usuario_form, usuarios=usuarios)


@app.route('/editar_usuario', methods=['POST'])
def editar_usuario():
    usuario_form = forms.UsuarioForm(request.form)
    id_usuario = request.form.get('editIdUsuario')
    usuario = Usuario.query.get(id_usuario)

    if usuario:
        usuario.nombre = usuario_form.nombre.data
        usuario.nombreUsuario = usuario_form.nombreUsuario.data
        contrasenia = usuario_form.contrasenia.data
        rol = usuario_form.rol.data
        telefono = usuario_form.telefono.data

        # Verificar si la contraseña ha sido modificada y cumple con las políticas de seguridad
        if contrasenia and not check_password_hash(usuario.contrasenia, contrasenia):
            if not password_pattern.match(contrasenia):
                flash('La contraseña debe contener al menos una mayúscula, una minúscula, un número y un carácter especial.', 'error')
                return redirect(url_for('usuarios'))

            if contrasenia in lista_contraseñas_no_seguras:
                flash('La contraseña no puede ser una contraseña por defecto o previamente utilizada.', 'error')
                return redirect(url_for('usuarios'))
            
            usuario.contrasenia = generate_password_hash(contrasenia)
            
        usuario.rol = rol
        usuario.telefono = telefono

        db.session.commit()
        flash('Usuario actualizado correctamente', 'success')
    else:
        flash('Usuario no encontrado', 'error')

    return redirect(url_for('usuarios'))
    
lista_contraseñas_no_seguras = [
    'password',
    '123456',
    'contraseña',
    
]
    
@app.route('/cambiar_estado_usuario/<int:id_usuario>', methods=['POST','GET'])
def cambiar_estado_usuario(id_usuario):
    usuario = Usuario.query.get(id_usuario)
    if usuario:
        usuario.estatus = 0  # Cambiar el estado del usuario a inactivo
        db.session.commit()
        flash('Usuario eliminado correctamente', 'success')
    else:
        flash('Usuario no encontrado', 'error')

    return redirect(url_for('usuarios'))


if __name__ == '__main__':
    csrf.init_app(app)
    db.init_app(app)
    with app.app_context():
        db.create_all()
        
    app.run()