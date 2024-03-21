from flask import Flask, request, render_template, flash, g, redirect, url_for, session, jsonify
from flask_wtf.csrf import CSRFProtect
from config import DevelopmentConfig
import forms
from models import db, Usuario
from sqlalchemy import func
from functools import wraps
from flask_cors import CORS
from flask_wtf.recaptcha import Recaptcha
import ssl
from datetime import datetime
from flask import session

ssl._create_default_https_context = ssl._create_unverified_context

app = Flask(__name__)
app.config.from_object(DevelopmentConfig)
csrf = CSRFProtect()
CORS(app, resources={r"/*": {"origins": app.config['CORS_ORIGINS']}})

recaptcha = Recaptcha(app)

@app.errorhandler(404)
def page_not_found(e):
    return render_template('404.html'),404

def login_required(f):
    @wraps(f)
    def decorated_function(*args, **kwargs):
        print(session)
        if 'logged_in' not in session:
            return redirect(url_for('login'))
        return f(*args, **kwargs)
    return decorated_function

@app.route('/', methods=['GET', 'POST'])
def login():
    usuario_form = forms.UsuarioForm(request.form)
    
    if request.method == 'POST' and usuario_form.validate():
        print(request.form)
        nombreUsuario = usuario_form.nombreUsuario.data
        contrasenia = usuario_form.contrasenia.data

        user = Usuario.query.filter_by(nombreUsuario=nombreUsuario).first()
        if user and user.contrasenia == contrasenia:
            session['logged_in'] = True
            #flash('Inicio de sesión exitoso', 'success')
            user.dateLastToken = datetime.utcnow()
            db.session.commit()
            return jsonify({'success': True, 'redirect': url_for('index')})
        else:
            #flash('Usuario o contraseña inválidos', 'error')
            return jsonify({'success': False, 'error': 'Usuario o contraseña inválidos'})
    
    return render_template('login.html', form=usuario_form)

@app.route('/logout', methods=['POST'])
def logout():
    session.clear()
    return redirect(url_for('login'))

@app.route('/index')
@login_required
def index():
    return render_template('index.html')

if __name__ == '__main__':
    csrf.init_app(app)
    db.init_app(app)
    with app.app_context():
        db.create_all()
        
    app.run()