from flask import Flask, request, render_template, flash, g, redirect, url_for, session, jsonify
from flask_wtf.csrf import CSRFProtect
from config import DevelopmentConfig
import forms, ssl
from models import db, Usuario, MateriaPrima
from sqlalchemy import func
from functools import wraps
from flask_cors import CORS
from flask_wtf.recaptcha import Recaptcha
from datetime import datetime
from flask_login import LoginManager, login_user, logout_user, login_required, login_manager
from werkzeug.security import generate_password_hash, check_password_hash

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
    usuario_form = forms.UsuarioForm(request.form)
    
    if request.method == 'POST' and usuario_form.validate():
        print(request.form)
        nombreUsuario = usuario_form.nombreUsuario.data
        contrasenia = usuario_form.contrasenia.data
        user = Usuario.query.filter_by(nombreUsuario=nombreUsuario).first()
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


if __name__ == '__main__':
    csrf.init_app(app)
    db.init_app(app)
    with app.app_context():
        db.create_all()
        
    app.run()