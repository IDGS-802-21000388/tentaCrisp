import forms, ssl, json, re, html2text, pandas, ast as pd, os, matplotlib
from flask import Flask, request, render_template, flash, redirect, url_for, jsonify, make_response, send_file , abort
from flask_wtf.csrf import CSRFProtect
from config import DevelopmentConfig
from models import db, Usuario, MateriaPrima, Proveedor, Producto, Detalle_producto, Detalle_materia_prima, Medida,LogsUser, Venta, DetalleVenta, Detalle_materia_prima, Detalle_producto, Proveedor, Merma, Compra, merma_inventario, solicitudProduccion
from sqlalchemy import func
from functools import wraps
from flask_cors import CORS , cross_origin
from datetime import datetime ,timedelta
from flask_login import current_user, LoginManager, login_user, logout_user, login_required, login_manager
from werkzeug.security import generate_password_hash, check_password_hash
ssl._create_default_https_context = ssl._create_unverified_context
from collections import defaultdict
import matplotlib.pyplot as plt
from matplotlib import pyplot as plt
from matplotlib.colors import ListedColormap
from reportlab.lib.pagesizes import letter
from reportlab.pdfgen import canvas
from reportlab.platypus import Table, TableStyle
from reportlab.lib import colors
from produccion.producir import producir_page
from usuarios.usuarios import usuarios_page
from dashboard.compras import compras_page
from dashboard.ventas import ventas_page
import matplotlib.pyplot as plt
from matplotlib.colors import hex2color, rgb2hex, colorConverter
import numpy as np
import pandas as pd

matplotlib.use('Agg')

app = Flask(__name__)
app.register_blueprint(producir_page, url_prefix='/produccion')
app.register_blueprint(usuarios_page)
app.register_blueprint(compras_page)
app.register_blueprint(ventas_page)


@app.before_request
def cors():
    if request.remote_addr != '127.0.0.1' :
        abort(403)
    
app.config.from_object(DevelopmentConfig)
csrf = CSRFProtect()
cors = CORS(app, resources={r"*": {"origins": "http://192.168.137.1:5000"}})
login_manager = LoginManager()
login_manager.init_app(app)

ssl._create_default_https_context = ssl._create_unverified_context
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

def admin_required(f):
    @wraps(f)
    def decorated_function(*args, **kwargs):
        if current_user.rol != 'Administrador':
            flash('No tienes permisos', 'warning')
            return redirect(url_for('index'))
        return f(*args, **kwargs)
    return decorated_function

def ventas_required(f):
    @wraps(f)
    def decorated_function(*args, **kwargs):
        print(current_user.rol)
        if current_user.rol == 'Administrador' or current_user.rol == 'Ventas':
            return f(*args, **kwargs)
        else:
            flash('No tienes permisos', 'warning')
            return redirect(url_for('index'))
        if current_user.rol != 'Administrador':
            if current_user.rol != 'Ventas' or current_user.rol != 'Administrador':
                flash('No tienes permisos', 'warning')
                return redirect(url_for('index'))
            return f(*args, **kwargs)
        return f(*args, **kwargs)
    return decorated_function

def produccion_required(f):
    @wraps(f)
    def decorated_function(*args, **kwargs):
        print(current_user.rol)
        if current_user.rol == 'Administrador' or current_user.rol == 'Produccion':
            return f(*args, **kwargs)
        else:
            flash('No tienes permisos', 'warning')
            return redirect(url_for('index'))
    return decorated_function

@app.route('/', methods=['GET', 'POST'])
@cross_origin()
def login():
    usuario_form = forms.LoginForm(request.form)
    
    if request.method == 'POST' and usuario_form.validate():
        fecha_hora_actual = datetime.now()
        fecha_hora_actual = fecha_hora_actual.replace(microsecond=0)

        nombreUsuario = str(html2text.html2text(usuario_form.nombreUsuario.data)).strip()
        contrasenia = str(html2text.html2text(usuario_form.contrasenia.data)).strip()
        hashed_password = generate_password_hash(contrasenia)
        user = Usuario.query.filter_by(nombreUsuario=nombreUsuario).first()
        intentos = user.intentos
        if user and check_password_hash(user.contrasenia, contrasenia) and int(intentos)<3: 
            login_user(user)
            log = LogsUser(
                procedimiento='Inicio de sesión',
                lastDate=fecha_hora_actual,
                idUsuario=user.idUsuario
            )
            db.session.add(log)
            db.session.commit()

            user.dateLastToken = fecha_hora_actual
            db.session.commit()
            return jsonify({'success': True, 'redirect': url_for('index')})
        else:
            if int(intentos)>=3:
                user.estatus = 0
                return jsonify({'success': False, 'error': 'Tu cuenta ha sido bloqueda.'})

            else:
                intentos+=1
                user.intentos = intentos
                db.session.commit()

                log = LogsUser(
                    procedimiento=f'Se intento Iniciar Sesión con las credenciales usuario:{nombreUsuario} y contraseña:{contrasenia} ',
                    lastDate=fecha_hora_actual,
                    idUsuario=0
                )
            
                db.session.add(log)
                db.session.commit()

                log = LogsUser(
                    procedimiento=f'Se intento Iniciar Sesión con las credenciales usuario:{nombreUsuario} y contraseña:{contrasenia} ',
                    lastDate=fecha_hora_actual,
                    idUsuario=0
                )

                return jsonify({'success': False, 'error': 'Usuario o contraseña inválidos'})
    
    return render_template('login.html', form=usuario_form)

@app.route('/logout', methods=['GET', 'POST'])
@login_required
def logout():
    logout_user()
    return redirect(url_for('login'))

@app.route('/index')
@login_required
def index():
    id_usuario_actual = current_user.idUsuario
    ultimo_inicio_sesion = LogsUser.query.filter_by(procedimiento='Inicio de sesión', idUsuario=id_usuario_actual).order_by(LogsUser.lastDate.desc()).offset(1).limit(1).first()
    return render_template('index.html', ultimo_inicio_sesion=ultimo_inicio_sesion)

# Inicio del Modulo de Proveedores

# Ruta para agregar una nuevo Proveedor
@app.route("/proveedor", methods=['GET', 'POST'])
@login_required
@admin_required
def proveedor():
    nombreProveedor = ""
    direccion = ""
    telefono = ""
    nombreAtiende = ""
    provedor = forms.ProveedorForm(request.form)

    if request.method == 'POST':
        if provedor.validate():
            nombreProveedor = provedor.nombreProveedor.data
            direccion = provedor.direccion.data
            telefono = provedor.telefono.data
            nombreAtiende = provedor.nombreAtiende.data

            nuevo_proveedor = Proveedor(nombreProveedor=nombreProveedor, direccion=direccion, telefono=telefono, nombreAtiende=nombreAtiende)
            
            try:
                db.session.add(nuevo_proveedor)
                db.session.commit()
                mensaje = "Proveedor agregado correctamente."
                flash(mensaje)
            except Exception as e:
                mensaje = "Error al agregar el proveedor a la base de datos: " + str(e)
                flash(mensaje)
        else:
            errores = {campo.name: campo.errors for campo in provedor}
            return jsonify({'success': False, 'errors': errores})

    proveedores = Proveedor.query.all()

    return render_template("provedor.html", form=provedor, proveedores=proveedores)

# Ruta para eliminar un Proveedor
@app.route("/eliminar_proveedor", methods=['POST'])
@login_required
def eliminar_proveedor():
    id_proveedor = int(request.form.get("id"))
    proveedor = Proveedor.query.get(id_proveedor)
    if proveedor:
        proveedor.estatus = 0  # Cambiar el estado del usuario a inactivo
        db.session.commit()
        mensaje = "Proveedor eliminado correctamente."
        flash(mensaje)
    else:
        mensaje = "Proveedor no encontrado."
        flash(mensaje)
    return redirect(url_for('proveedor'))

# Ruta para editar un Proveedor
@app.route('/editar_proveedor', methods=['POST'])
@login_required
def editar_proveedor():
    provedor = forms.ProveedorForm(request.form)
    id_proveedor = request.form.get('editIdProveedor')
    proveedor = Proveedor.query.get(id_proveedor)
    nombreProveedor = provedor.nombreProveedor.data
    direccion = provedor.direccion.data
    telefono = provedor.telefono.data
    nombreAtiende = provedor.nombreAtiende.data

    if proveedor:
        proveedor.nombreProveedor = nombreProveedor
        proveedor.direccion = direccion
        proveedor.telefono = telefono
        proveedor.nombreAtiende = nombreAtiende

        try:
            db.session.commit()
            mensaje = "Proveedor editado correctamente."
            flash(mensaje)
        except Exception as e:
            mensaje = "Error al editar el proveedor a la base de datos: " + str(e)
            flash(mensaje)
    else:
        flash('Proveedor no encontrado', 'error')

    return redirect(url_for('proveedor'))

# Fin del Modulo de Proveedores

# Inicio del Modulo de Materia Prima
@app.route("/inventario", methods=['GET', 'POST'])
@login_required
def inventario():
    nombreMateria = ""
    precio = ""
    cantidad = ""
    tipo_compra = ""
    fechaVen = ""
    idMedida = ""
    gramos_ajustados = ""
    porcentaje = 0
    inventario = forms.InventarioForm(request.form)
    proveedores = Proveedor.query.all()
    if request.method == 'POST':
        nombreMateria = inventario.nombre.data
        precio = inventario.precio.data
        cantidad = inventario.cantidad.data
        tipo_compra = request.form.get('tipo_compra')
        fechaVen = inventario.fechaVen.data
        fechaCom = datetime.now()
        proveedor_id = request.form.get('proveedor')
        campoKilosBulto = request.form.get('kilos_bulto')
        campoKilosCaja = request.form.get('numero_piezas_caja')
        
        #Tupla de Productos con cascara por porcentaje
        ingredientes_con_cascara_porcentaje = [
            ("Naranja", 20),
            ("Cereza en almíbar", 5),
            ("Nuez picada", 20),
            ("Huevo", 11)
        ]
        #Tupla de Productos Liquidos por militros
        ingredientes_liquidos = [
            ("Leche", 1000),
            ("Vainilla", 560)
        ]
        #Tupla de Valores por Unidad
        ingredientes_con_valores = [
            ("Azúcar", 1000),  # 1 kilogramo de azúcar
            ("Mantequilla", 1000),  # 1 kilogramo de mantequilla
            ("Bicarbonato de sodio", 300),  # 300 gramos de bicarbonato de sodio
            ("Harina de Trigo", 1000),  # 1 kilogramo de harina de trigo
            ("Huevo", 1900),  # 1.9 kilogramos de huevos
            ("Cerezas en almíbar", 3500),  # 3.5 kilogramos de cerezas en almíbar
            ("Nueces", 1000),  # 1 kilogramo de nueces
            ("Sal", 1000),  # 1 kilogramo de sal
            ("Leche en polvo", 2700),  # 2.7 kilogramos de leche en polvo
            ("Manteca vegetal", 1000),  # 1 kilogramo de manteca vegetal
            ("Polvo para hornear", 1000),  # 1 kilogramo de polvo para hornear
            ("Harina integral", 1000),  # 1 kilogramo de harina integral
            ("Copos de avena", 1000),  # 1 kilogramo de copos de avena
            ("Azúcar moreno", 1000),  # 1 kilogramo de azúcar moreno
            ("Vainilla", 500),  # 500 mililitros de esencia de vainilla
            ("Chispas de chocolate", 500),  # 500 gramos de chispas de chocolate
            ("Hojuelas de avena", 1000),  # 1 kilogramo de hojuelas de avena
            ("Cerezas", 580),  # 580 gramos de cerezas
            ("Leche", 1000),  # 1 litro de leche
            ("Mermelada de fresa", 980),  # 980 gramos de mermelada de fresa
            ("Harina", 1000),
            ("Azucar Glass", 1000)
        ]
        #Tupla de Ingredientes de bultos
        ingredientes_de_bultos = [
            "Azucar",
            "Harina",
            "Azucar Glass",
            "Sal",
            "Harina de Trigo",
            "Naranja",
            "Polvo para Hornear",
            "Canela",
            "Harina Integral",
            "Azucar Morena",
            "Hojuelas de Avena",
        ]
        #Tupla de Ingredientes de cajas
        ingredientes_de_caja = [
            ("Mantequilla",24),
            ("Huevo",22),
            ("Manteca Vegetal",24),
            ("Manteca de Cerdo",24),
            ("Copoz de Avena",40)
        ]

        if tipo_compra == 'bulto':
            if nombreMateria in ingredientes_de_bultos:
                if nombreMateria in [nombre for nombre, valor_unidad in ingredientes_con_valores]:
                    valor_unidad = [valor_unidad for nombre, valor_unidad in ingredientes_con_valores if nombre == nombreMateria][0]
                    if nombreMateria in [nombre for nombre, porcentaje in ingredientes_con_cascara_porcentaje]:
                        porcentaje_cascara = [porcentaje for nombre, porcentaje in ingredientes_con_cascara_porcentaje if nombre == nombreMateria][0]

                        gramos_ajustados = float(cantidad) * float(campoKilosBulto) - (float(cantidad) * float(campoKilosBulto) * float(porcentaje_cascara) / 100)
                        flash("Kilos ajustados Bulto" , gramos_ajustados)
                        porcentaje = float((gramos_ajustados / (float(valor_unidad) * 50)) * 100)
                        if nombreMateria == "Leche" or nombreMateria == "Vainilla":
                            idMedida = 3
                        elif nombreMateria == "Huevo":
                            idMedida = 1
                        else:
                            idMedida = 2

                        nueva_materia_prima = MateriaPrima(
                            nombreMateria=nombreMateria,
                            precioCompra=precio,
                            cantidad=cantidad,
                            idMedida=idMedida,
                            idProveedor=proveedor_id
                        )
                        db.session.add(nueva_materia_prima)

                        try:
                            db.session.commit()
                            mensaje = "Materia Prima agregada correctamente."
                            flash(mensaje)
                        except Exception as e:
                            mensaje = "Error al agregar la materia prima a la base de datos: " + str(e)
                            flash(mensaje)
                        
                        ultimo_id_materia_prima = MateriaPrima.query.order_by(MateriaPrima.idMateriaPrima.desc()).first().idMateriaPrima
                        nuevo_detalle_materia_prima = Detalle_materia_prima(
                            fechaCompra=fechaCom,
                            fechaVencimiento=fechaVen,
                            cantidadExistentes=gramos_ajustados,
                            idMateriaPrima=ultimo_id_materia_prima,
                            porcentaje=porcentaje)

                        db.session.add(nuevo_detalle_materia_prima)

                        try:
                            db.session.commit()
                            flash("Detalle de materia prima agregado correctamente.")
                            ultimo_id_materia_prima = MateriaPrima.query.order_by(MateriaPrima.idMateriaPrima.desc()).first().idMateriaPrima
                            ultimo_id_detalle_materia_prima = Detalle_materia_prima.query.order_by(Detalle_materia_prima.idDetalle_materia_prima.desc()).first().idDetalle_materia_prima

                            nueva_compra = Compra(
                                idMateriaPrima=ultimo_id_materia_prima,
                                idDetalle_materia_prima=ultimo_id_detalle_materia_prima,
                                cantidadExistentes=gramos_ajustados
                            )

                            db.session.add(nueva_compra)
                            try:
                                db.session.commit()
                                flash("Detalle de compra agregado correctamente.")
                            except Exception as e:
                                db.session.rollback()
                                flash("Error al agregar compra a la base de datos: " + str(e))
                        except Exception as e:
                            db.session.rollback()
                            flash("Error al agregar el detalle de materia prima a la base de datos: " + str(e))
                        
                        
                    else:
                        gramos_ajustados = valor_unidad * (float(cantidad) * float(campoKilosBulto))

                        if nombreMateria == "Leche" or nombreMateria == "Vainilla":
                            idMedida = 3
                        elif nombreMateria == "Huevo":
                            idMedida = 1
                        else:
                            idMedida = 2

                        nueva_materia_prima = MateriaPrima(
                            nombreMateria=nombreMateria,
                            precioCompra=precio,
                            cantidad=cantidad,
                            idMedida=idMedida,
                            idProveedor=proveedor_id
                        )
                        db.session.add(nueva_materia_prima)

                        try:
                            db.session.commit()
                            mensaje = "Materia Prima agregada correctamente."
                            flash(mensaje)
                        except Exception as e:
                            mensaje = "Error al agregar la materia prima a la base de datos: " + str(e)
                            flash(mensaje)
                        
                        ultimo_id_materia_prima = MateriaPrima.query.order_by(MateriaPrima.idMateriaPrima.desc()).first().idMateriaPrima
                        nuevo_detalle_materia_prima = Detalle_materia_prima(
                            fechaCompra=fechaCom,
                            fechaVencimiento=fechaVen,
                            cantidadExistentes=gramos_ajustados,
                            idMateriaPrima=ultimo_id_materia_prima,
                            porcentaje=porcentaje)

                        db.session.add(nuevo_detalle_materia_prima)

                        try:
                            db.session.commit()
                            flash("Detalle de materia prima agregado correctamente.")
                            ultimo_id_materia_prima = MateriaPrima.query.order_by(MateriaPrima.idMateriaPrima.desc()).first().idMateriaPrima
                            ultimo_id_detalle_materia_prima = Detalle_materia_prima.query.order_by(Detalle_materia_prima.idDetalle_materia_prima.desc()).first().idDetalle_materia_prima

                            nueva_compra = Compra(
                                idMateriaPrima=ultimo_id_materia_prima,
                                idDetalle_materia_prima=ultimo_id_detalle_materia_prima,
                                cantidadExistentes=gramos_ajustados
                            )

                            db.session.add(nueva_compra)
                            try:
                                db.session.commit()
                                flash("Detalle de compra agregado correctamente.")
                            except Exception as e:
                                db.session.rollback()
                                flash("Error al agregar compra a la base de datos: " + str(e))
                        except Exception as e:
                            db.session.rollback()
                            flash("Error al agregar el detalle de materia prima a la base de datos: " + str(e))
                        
                        
                        
                else:
                    flash("Este ingrediente no puede ser encontrado.")
            else:
                flash("Este ingrediente no puede ser comprado en bulto.")
        elif tipo_compra == 'caja':
            if nombreMateria in [nombre for nombre, _ in ingredientes_de_caja]:
                if nombreMateria in [nombre for nombre, valor_unidad in ingredientes_con_valores]:
                    valor_unidad = [valor_unidad for nombre, valor_unidad in ingredientes_con_valores if nombre == nombreMateria][0]
                    if nombreMateria in [nombre for nombre, porcentaje in ingredientes_con_cascara_porcentaje]:
                        porcentaje_cascara = [porcentaje for nombre, porcentaje in ingredientes_con_cascara_porcentaje if nombre == nombreMateria][0]
                        datos_sin_porcentaje = float(campoKilosCaja) * float(valor_unidad)
                        datos_de_porcentaje = (datos_sin_porcentaje * float(porcentaje_cascara) / 100)
                        gramos_ajustados = datos_sin_porcentaje - datos_de_porcentaje
                        porcentaje = float((gramos_ajustados / (float(valor_unidad) * 50)) * 100)

                        if nombreMateria == "Leche" or nombreMateria == "Vainilla":
                            idMedida = 3
                        elif nombreMateria == "Huevo":
                            idMedida = 1
                        else:
                            idMedida = 2

                        nueva_materia_prima = MateriaPrima(
                            nombreMateria=nombreMateria,
                            precioCompra=precio,
                            cantidad=cantidad,
                            idMedida=idMedida,
                            idProveedor=proveedor_id
                        )
                        db.session.add(nueva_materia_prima)

                        try:
                            db.session.commit()
                            mensaje = "Materia Prima agregada correctamente."
                            flash(mensaje)
                        except Exception as e:
                            mensaje = "Error al agregar la materia prima a la base de datos: " + str(e)
                            flash(mensaje)
                        
                        ultimo_id_materia_prima = MateriaPrima.query.order_by(MateriaPrima.idMateriaPrima.desc()).first().idMateriaPrima
                        nuevo_detalle_materia_prima = Detalle_materia_prima(
                            fechaCompra=fechaCom,
                            fechaVencimiento=fechaVen,
                            cantidadExistentes=gramos_ajustados,
                            idMateriaPrima=ultimo_id_materia_prima,
                            porcentaje=porcentaje)

                        db.session.add(nuevo_detalle_materia_prima)

                        try:
                            db.session.commit()
                            flash("Detalle de materia prima agregado correctamente.")
                            ultimo_id_materia_prima = MateriaPrima.query.order_by(MateriaPrima.idMateriaPrima.desc()).first().idMateriaPrima
                            ultimo_id_detalle_materia_prima = Detalle_materia_prima.query.order_by(Detalle_materia_prima.idDetalle_materia_prima.desc()).first().idDetalle_materia_prima

                            nueva_compra = Compra(
                                idMateriaPrima=ultimo_id_materia_prima,
                                idDetalle_materia_prima=ultimo_id_detalle_materia_prima,
                                cantidadExistentes=gramos_ajustados
                            )

                            db.session.add(nueva_compra)
                            try:
                                db.session.commit()
                                flash("Detalle de compra agregado correctamente.")
                            except Exception as e:
                                db.session.rollback()
                                flash("Error al agregar compra a la base de datos: " + str(e))
                        except Exception as e:
                            db.session.rollback()
                            flash("Error al agregar el detalle de materia prima a la base de datos: " + str(e))

                        
                        
                            
                    else:
                        gramos_ajustados = valor_unidad * (float(cantidad))
                        if nombreMateria == "Leche" or nombreMateria == "Vainilla":
                            idMedida = 3
                        elif nombreMateria == "Huevo":
                            idMedida = 1
                        else:
                            idMedida = 2

                        nueva_materia_prima = MateriaPrima(
                            nombreMateria=nombreMateria,
                            precioCompra=precio,
                            cantidad=cantidad,
                            idMedida=idMedida,
                            idProveedor=proveedor_id
                        )
                        db.session.add(nueva_materia_prima)

                        try:
                            db.session.commit()
                            mensaje = "Materia Prima agregada correctamente."
                            flash(mensaje)
                        except Exception as e:
                            mensaje = "Error al agregar la materia prima a la base de datos: " + str(e)
                            flash(mensaje)
                        
                        ultimo_id_materia_prima = MateriaPrima.query.order_by(MateriaPrima.idMateriaPrima.desc()).first().idMateriaPrima
                        nuevo_detalle_materia_prima = Detalle_materia_prima(
                            fechaCompra=fechaCom,
                            fechaVencimiento=fechaVen,
                            cantidadExistentes=gramos_ajustados,
                            idMateriaPrima=ultimo_id_materia_prima,
                            porcentaje=porcentaje)

                        db.session.add(nuevo_detalle_materia_prima)

                        try:
                            db.session.commit()
                            flash("Detalle de materia prima agregado correctamente.")
                            ultimo_id_materia_prima = MateriaPrima.query.order_by(MateriaPrima.idMateriaPrima.desc()).first().idMateriaPrima
                            ultimo_id_detalle_materia_prima = Detalle_materia_prima.query.order_by(Detalle_materia_prima.idDetalle_materia_prima.desc()).first().idDetalle_materia_prima

                            nueva_compra = Compra(
                                idMateriaPrima=ultimo_id_materia_prima,
                                idDetalle_materia_prima=ultimo_id_detalle_materia_prima,
                                cantidadExistentes=gramos_ajustados
                            )

                            db.session.add(nueva_compra)
                            try:
                                db.session.commit()
                                flash("Detalle de compra agregado correctamente.")
                            except Exception as e:
                                db.session.rollback()
                                flash("Error al agregar compra a la base de datos: " + str(e))
                        except Exception as e:
                            db.session.rollback()
                            flash("Error al agregar el detalle de materia prima a la base de datos: " + str(e))
                        
                        
                        
                            
                else:
                    flash("Este ingrediente no puede ser encontrado.")
            else:
                flash("Este ingrediente no puede ser comprado por caja.")
        elif tipo_compra == 'unidad':
            if nombreMateria in [nombre for nombre, _ in ingredientes_con_valores]:
                valor_unidad = [valor_unidad for nombre, valor_unidad in ingredientes_con_valores if nombre == nombreMateria][0]
                gramos_ajustados = float(cantidad) * float(valor_unidad)
                if nombreMateria in [nombre for nombre, porcentaje in ingredientes_con_cascara_porcentaje]:
                    porcentaje_cascara = [porcentaje for nombre, porcentaje in ingredientes_con_cascara_porcentaje if nombre == nombreMateria][0]
                    gramos_ajustados -= (float(cantidad) * float(valor_unidad) * float(porcentaje_cascara) / 100)
                    if float(valor_unidad) != 0:
                        porcentaje = float((gramos_ajustados / (float(valor_unidad) * 50)) * 100)
                        if nombreMateria == "Leche" or nombreMateria == "Vainilla":
                            idMedida = 3
                        elif nombreMateria == "Huevo":
                            idMedida = 1
                        else:
                            idMedida = 2

                        nueva_materia_prima = MateriaPrima(
                            nombreMateria=nombreMateria,
                            precioCompra=precio,
                            cantidad=cantidad,
                            idMedida=idMedida,
                            idProveedor=proveedor_id
                        )
                        db.session.add(nueva_materia_prima)

                        try:
                            db.session.commit()
                            mensaje = "Materia Prima agregada correctamente."
                            flash(mensaje)
                        except Exception as e:
                            mensaje = "Error al agregar la materia prima a la base de datos: " + str(e)
                            flash(mensaje)
                        
                        ultimo_id_materia_prima = MateriaPrima.query.order_by(MateriaPrima.idMateriaPrima.desc()).first().idMateriaPrima
                        nuevo_detalle_materia_prima = Detalle_materia_prima(
                            fechaCompra=fechaCom,
                            fechaVencimiento=fechaVen,
                            cantidadExistentes=gramos_ajustados,
                            idMateriaPrima=ultimo_id_materia_prima,
                            porcentaje=porcentaje)

                        db.session.add(nuevo_detalle_materia_prima)

                        try:
                            db.session.commit()
                            flash("Detalle de materia prima agregado correctamente.")
                            ultimo_id_materia_prima = MateriaPrima.query.order_by(MateriaPrima.idMateriaPrima.desc()).first().idMateriaPrima
                            ultimo_id_detalle_materia_prima = Detalle_materia_prima.query.order_by(Detalle_materia_prima.idDetalle_materia_prima.desc()).first().idDetalle_materia_prima

                            nueva_compra = Compra(
                                idMateriaPrima=ultimo_id_materia_prima,
                                idDetalle_materia_prima=ultimo_id_detalle_materia_prima,
                                cantidadExistentes=gramos_ajustados
                            )

                            db.session.add(nueva_compra)
                            try:
                                db.session.commit()
                                flash("Detalle de compra agregado correctamente.")
                            except Exception as e:
                                db.session.rollback()
                                flash("Error al agregar compra a la base de datos: " + str(e))
                        except Exception as e:
                            db.session.rollback()
                            flash("Error al agregar el detalle de materia prima a la base de datos: " + str(e))
                            
                        
                        
                            
                else:
                    gramos_ajustados = valor_unidad * (float(cantidad))
                    if nombreMateria == "Leche" or nombreMateria == "Vainilla":
                            idMedida = 3
                    elif nombreMateria == "Huevo":
                        idMedida = 1
                    else:
                        idMedida = 2

                    nueva_materia_prima = MateriaPrima(
                        nombreMateria=nombreMateria,
                        precioCompra=precio,
                        cantidad=cantidad,
                        idMedida=idMedida,
                        idProveedor=proveedor_id
                    )
                    db.session.add(nueva_materia_prima)

                    try:
                        db.session.commit()
                        mensaje = "Materia Prima agregada correctamente."
                        flash(mensaje)
                    except Exception as e:
                        mensaje = "Error al agregar la materia prima a la base de datos: " + str(e)
                        flash(mensaje)
                    
                    ultimo_id_materia_prima = MateriaPrima.query.order_by(MateriaPrima.idMateriaPrima.desc()).first().idMateriaPrima
                    nuevo_detalle_materia_prima = Detalle_materia_prima(
                        fechaCompra=fechaCom,
                        fechaVencimiento=fechaVen,
                        cantidadExistentes=gramos_ajustados,
                        idMateriaPrima=ultimo_id_materia_prima,
                        porcentaje=porcentaje)

                    db.session.add(nuevo_detalle_materia_prima)

                    try:
                        db.session.commit()
                        flash("Detalle de materia prima agregado correctamente.")
                        ultimo_id_materia_prima = MateriaPrima.query.order_by(MateriaPrima.idMateriaPrima.desc()).first().idMateriaPrima
                        ultimo_id_detalle_materia_prima = Detalle_materia_prima.query.order_by(Detalle_materia_prima.idDetalle_materia_prima.desc()).first().idDetalle_materia_prima

                        nueva_compra = Compra(
                                idMateriaPrima=ultimo_id_materia_prima,
                                idDetalle_materia_prima=ultimo_id_detalle_materia_prima,
                                cantidadExistentes=gramos_ajustados
                            )

                        db.session.add(nueva_compra)
                        try:
                            db.session.commit()
                            flash("Detalle de compra agregado correctamente.")
                        except Exception as e:
                            db.session.rollback()
                            flash("Error al agregar compra a la base de datos: " + str(e))
                    except Exception as e:
                        db.session.rollback()
                        flash("Error al agregar el detalle de materia prima a la base de datos: " + str(e))
                        
                    
                        
                            
            else:
                
                flash("Este ingrediente no puede ser comprado por unidad.")
        else:
            flash("Tipo de compra no válido.")
    

    materias_primas = MateriaPrima.query.all()
    detalle_primas = Detalle_materia_prima.query.filter_by(estatus=1).all()
    proveedores = Proveedor.query.all()
    medida = Medida.query.all()

    datos_procesados = procesar_datos(materias_primas, detalle_primas)
    
    materias_agotadas = set()
    for materia_prima in materias_primas:
        for detalle in detalle_primas:
            nombre_materia = materia_prima.nombreMateria
            cantidad_existentes = detalle.cantidadExistentes
            
            if cantidad_existentes <= 600:
                materias_agotadas.add(nombre_materia)

    mensaje_alerta = "\n".join([f"{materia} - Cantidad: {cantidad_existentes}" for materia in materias_agotadas])
    if mensaje_alerta:
        flash("Ingredientes agotados o por agotarse próximamente:\n" + mensaje_alerta)


    return render_template("vista_Inventario.html", datos_procesados=datos_procesados, form=inventario, materias_primas=materias_primas, proveedores=proveedores, detalle_primas=detalle_primas, medida=medida)

def procesar_datos(materias_primas, detalles_primas):
    detalles_por_materia = defaultdict(list)
    for detalle in detalles_primas:
        detalles_por_materia[detalle.idMateriaPrima].append(detalle)
    datos_procesados_dict = defaultdict(lambda: {'cantidad_existente': 0, 'fecha_vencimiento': None, 'porcentaje': None})

    for materia_prima in materias_primas:
        detalles = detalles_por_materia[materia_prima.idMateriaPrima]

        if detalles:
            cantidad_existente = sum(detalle.cantidadExistentes for detalle in detalles)
            fecha_vencimiento = max(detalle.fechaVencimiento for detalle in detalles if detalle.fechaVencimiento is not None)
            porcentaje_suma = sum(detalle.porcentaje for detalle in detalles if detalle.porcentaje is not None)
        else:
            cantidad_existente = 0
            fecha_vencimiento = None
            porcentaje_suma = 0 

        datos_procesados_dict[materia_prima.nombreMateria]['cantidad_existente'] += cantidad_existente
        if fecha_vencimiento:
            if not datos_procesados_dict[materia_prima.nombreMateria]['fecha_vencimiento'] or fecha_vencimiento > datos_procesados_dict[materia_prima.nombreMateria]['fecha_vencimiento']:
                datos_procesados_dict[materia_prima.nombreMateria]['fecha_vencimiento'] = fecha_vencimiento
        datos_procesados_dict[materia_prima.nombreMateria]['porcentaje'] = porcentaje_suma
    datos_procesados = [{'nombre': nombre, **datos} for nombre, datos in datos_procesados_dict.items()]

    return datos_procesados

@app.route('/editar_inventario', methods=['POST'])
@login_required
def editar_inventario():
    nombreMateria = ""
    precio = ""
    cantidad = ""
    tipo_compra = ""
    fechaVen = ""
    idMedida = ""
    gramos_ajustados = ""
    porcentaje = 0
    inventario = forms.InventarioForm(request.form)
    id_materiaPrima = request.form.get('editIdMateria')
    if request.method == 'POST':
        nombreMateria = inventario.nombre.data
        precio = inventario.precio.data
        cantidad = inventario.cantidad.data
        tipo_compra = request.form.get('tipo_compraEdit')
        fechaVen = inventario.fechaVen.data
        fechaCom = datetime.now()
        proveedor_id = request.form.get('proveedor')
        campoKilosBulto = request.form.get('kilos_bulto_edit')
        campoKilosCaja = request.form.get('numero_piezas_caja_edit')
        
        #Tupla de Productos con cascara por porcentaje
        ingredientes_con_cascara_porcentaje = [
            ("Naranja", 20),
            ("Cereza en almíbar", 5),
            ("Nuez picada", 20),
            ("Huevo", 11)
        ]
        #Tupla de Productos Liquidos por militros
        ingredientes_liquidos = [
            ("Leche", 1000),
            ("Vainilla", 560)
        ]
        #Tupla de Valores por Unidad
        ingredientes_con_valores = [
            ("Azúcar", 1000),  # 1 kilogramo de azúcar
            ("Mantequilla", 1000),  # 1 kilogramo de mantequilla
            ("Bicarbonato de sodio", 300),  # 300 gramos de bicarbonato de sodio
            ("Harina de Trigo", 1000),  # 1 kilogramo de harina de trigo
            ("Huevo", 1900),  # 1.9 kilogramos de huevos
            ("Cerezas en almíbar", 3500),  # 3.5 kilogramos de cerezas en almíbar
            ("Nueces", 1000),  # 1 kilogramo de nueces
            ("Sal", 1000),  # 1 kilogramo de sal
            ("Leche en polvo", 2700),  # 2.7 kilogramos de leche en polvo
            ("Manteca vegetal", 1000),  # 1 kilogramo de manteca vegetal
            ("Polvo para hornear", 1000),  # 1 kilogramo de polvo para hornear
            ("Harina integral", 1000),  # 1 kilogramo de harina integral
            ("Copos de avena", 1000),  # 1 kilogramo de copos de avena
            ("Azúcar moreno", 1000),  # 1 kilogramo de azúcar moreno
            ("Vainilla", 500),  # 500 mililitros de esencia de vainilla
            ("Chispas de chocolate", 500),  # 500 gramos de chispas de chocolate
            ("Hojuelas de avena", 1000),  # 1 kilogramo de hojuelas de avena
            ("Cerezas", 580),  # 580 gramos de cerezas
            ("Leche", 1000),  # 1 litro de leche
            ("Mermelada de fresa", 980),  # 980 gramos de mermelada de fresa
            ("Harina", 1000),
            ("Azucar Glass", 1000),
        ]
        #Tupla de Ingredientes de bultos
        ingredientes_de_bultos = [
            "Azucar",
            "Harina",
            "Azucar Glass",
            "Sal",
            "Harina de Trigo",
            "Naranja",
            "Polvo para Hornear",
            "Canela",
            "Harina Integral",
            "Azucar Morena",
            "Hojuelas de Avena",
        ]
        #Tupla de Ingredientes de cajas
        ingredientes_de_caja = [
            ("Mantequilla",24),
            ("Huevo",22),
            ("Manteca Vegetal",24),
            ("Manteca de Cerdo",24),
            ("Copoz de Avena",40)
        ]


        if tipo_compra == 'bulto':
            if nombreMateria in ingredientes_de_bultos:
                if nombreMateria in [nombre for nombre, valor_unidad in ingredientes_con_valores]:
                    valor_unidad = [valor_unidad for nombre, valor_unidad in ingredientes_con_valores if nombre == nombreMateria][0]
                    if nombreMateria in [nombre for nombre, porcentaje in ingredientes_con_cascara_porcentaje]:
                        porcentaje_cascara = [porcentaje for nombre, porcentaje in ingredientes_con_cascara_porcentaje if nombre == nombreMateria][0]

                        gramos_ajustados = float(cantidad) * float(campoKilosBulto) - (float(cantidad) * float(campoKilosBulto) * float(porcentaje_cascara) / 100)
                        porcentaje = float((kilos_ajustados/float(valor_unidad*50))*100)
                        if nombreMateria in ingredientes_liquidos:
                            idMedida = 3
                        elif nombreMateria == "Huevo":
                            idMedida = 1
                        else:
                            idMedida = 2

                        materia_prima_existente = MateriaPrima.query.get(id_materiaPrima)

                        if materia_prima_existente:
                            materia_prima_existente.nombreMateria = nombreMateria
                            materia_prima_existente.precioCompra = precio
                            materia_prima_existente.cantidad = cantidad
                            materia_prima_existente.idMedida = idMedida
                            materia_prima_existente.idProveedor = proveedor_id

                            try:
                                db.session.commit()
                                flash("Materia prima actualizada correctamente.")
                            except Exception as e:
                                db.session.rollback()
                                flash("Error al actualizar la materia prima en la base de datos: " + str(e))
                        else:
                            flash("La materia prima proporcionado no existe en la base de datos.")

                        detalle_existente = Detalle_materia_prima.query.filter_by(idMateriaPrima=id_materiaPrima).first()

                        if detalle_existente:

                            detalle_existente.fechaCompra = fechaCom
                            detalle_existente.fechaVencimiento = fechaVen
                            detalle_existente.cantidadExistentes = gramos_ajustados
                            detalle_existente.porcentaje = porcentaje

                            try:
                                db.session.commit()
                            except Exception as e:
                                db.session.rollback()
                                flash("Error al actualizar el detalle de materia prima en la base de datos: " + str(e))
                        else:
                            flash("El detalle de materia prima correspondiente al ID proporcionado no existe en la base de datos.")
                    else:
                        kilos_ajustados = valor_unidad * (float(cantidad) * float(campoKilosBulto))
                        if nombreMateria in ingredientes_liquidos:
                            idMedida = 3
                        elif nombreMateria == "Huevo":
                            idMedida = 1
                        else:
                            idMedida = 2

                        materia_prima_existente = MateriaPrima.query.get(id_materiaPrima)

                        if materia_prima_existente:
                            materia_prima_existente.nombreMateria = nombreMateria
                            materia_prima_existente.precioCompra = precio
                            materia_prima_existente.cantidad = cantidad
                            materia_prima_existente.idMedida = idMedida
                            materia_prima_existente.idProveedor = proveedor_id

                            try:
                                db.session.commit()
                                flash("Materia prima actualizada correctamente.")
                            except Exception as e:
                                db.session.rollback()
                        else:
                            flash("La materia prima con el ID proporcionado no existe en la base de datos.")

                        detalle_existente = Detalle_materia_prima.query.filter_by(idMateriaPrima=id_materiaPrima).first()

                        if detalle_existente:

                            detalle_existente.fechaCompra = fechaCom
                            detalle_existente.fechaVencimiento = fechaVen
                            detalle_existente.cantidadExistentes = kilos_ajustados
                            detalle_existente.porcentaje = porcentaje

                            try:
                                db.session.commit()
                            except Exception as e:
                                db.session.rollback()
                                flash("Error al actualizar el detalle de materia prima en la base de datos: " + str(e))
                        else:
                            flash("El detalle de materia prima correspondiente al ID proporcionado no existe en la base de datos.")
                else:
                    flash("Este ingrediente no puede ser encontrado.")
            else:
                flash("Este ingrediente no puede ser comprado en bulto.")
        elif tipo_compra == 'caja':
            if nombreMateria in [nombre for nombre, _ in ingredientes_de_caja]:
                if nombreMateria in [nombre for nombre, valor_unidad in ingredientes_con_valores]:
                    valor_unidad = [valor_unidad for nombre, valor_unidad in ingredientes_con_valores if nombre == nombreMateria][0]
                    if nombreMateria in [nombre for nombre, porcentaje in ingredientes_con_cascara_porcentaje]:
                        porcentaje_cascara = [porcentaje for nombre, porcentaje in ingredientes_con_cascara_porcentaje if nombre == nombreMateria][0]
                        datos_sin_porcentaje= float(campoKilosCaja) * float(valor_unidad)
                        datos_de_porcentaje = (datos_sin_porcentaje * float(porcentaje_cascara) / 100)
                        gramos_ajustados =datos_sin_porcentaje - datos_de_porcentaje
                        porcentaje = float((gramos_ajustados/float(valor_unidad*50))*100)
                        if nombreMateria == "Leche" or nombreMateria == "Vainilla":
                            idMedida = 3
                        elif nombreMateria == "Huevo":
                            idMedida = 1
                        else:
                            idMedida = 2

                        materia_prima_existente = MateriaPrima.query.get(id_materiaPrima)

                        if materia_prima_existente:
                            materia_prima_existente.nombreMateria = nombreMateria
                            materia_prima_existente.precioCompra = precio
                            materia_prima_existente.cantidad = cantidad
                            materia_prima_existente.idMedida = idMedida
                            materia_prima_existente.idProveedor = proveedor_id

                            try:
                                db.session.commit()
                                flash("Materia prima actualizada correctamente.")
                            except Exception as e:
                                db.session.rollback()
                                flash("Error al actualizar la materia prima en la base de datos: " + str(e))
                        else:
                            flash("La materia prima con el ID proporcionado no existe en la base de datos.")

                        detalle_existente = Detalle_materia_prima.query.filter_by(idMateriaPrima=id_materiaPrima).first()

                        if detalle_existente:

                            detalle_existente.fechaCompra = fechaCom
                            detalle_existente.fechaVencimiento = fechaVen
                            detalle_existente.cantidadExistentes = gramos_ajustados
                            detalle_existente.porcentaje = porcentaje

                            try:
                                db.session.commit()
                                flash("Detalle de materia prima actualizado correctamente.")
                            except Exception as e:
                                db.session.rollback()
                                flash("Error al actualizar el detalle de materia prima en la base de datos: " + str(e))
                        else:
                            flash("El detalle de materia prima correspondiente al ID proporcionado no existe en la base de datos.")
                    else:
                        gramos_ajustados = valor_unidad * (float(cantidad) * float(valor_unidad))
                        if nombreMateria == "Leche" or nombreMateria == "Vainilla":
                            idMedida = 3
                        elif nombreMateria == "Huevo":
                            idMedida = 1
                        else:
                            idMedida = 2

                        materia_prima_existente = MateriaPrima.query.get(id_materiaPrima)

                        if materia_prima_existente:
                            materia_prima_existente.nombreMateria = nombreMateria
                            materia_prima_existente.precioCompra = precio
                            materia_prima_existente.cantidad = cantidad
                            materia_prima_existente.idMedida = idMedida
                            materia_prima_existente.idProveedor = proveedor_id

                            try:
                                db.session.commit()
                                flash("Materia prima actualizada correctamente.")
                            except Exception as e:
                                db.session.rollback()
                                flash("Error al actualizar la materia prima en la base de datos: " + str(e))
                        else:
                            flash("La materia prima con el ID proporcionado no existe en la base de datos.")

                        detalle_existente = Detalle_materia_prima.query.filter_by(idMateriaPrima=id_materiaPrima).first()

                        if detalle_existente:

                            detalle_existente.fechaCompra = fechaCom
                            detalle_existente.fechaVencimiento = fechaVen
                            detalle_existente.cantidadExistentes = gramos_ajustados
                            detalle_existente.porcentaje = porcentaje

                            try:
                                db.session.commit()
                                flash("Detalle de materia prima actualizado correctamente.")
                            except Exception as e:
                                db.session.rollback()
                                flash("Error al actualizar el detalle de materia prima en la base de datos: " + str(e))
                        else:
                            flash("El detalle de materia prima correspondiente al ID proporcionado no existe en la base de datos.")
                else:
                    flash("Este ingrediente no puede ser encontrado.")
            else:
                flash("Este ingrediente no puede ser comprado por caja.")
        elif tipo_compra == 'unidad':
            if nombreMateria in [nombre for nombre, _ in ingredientes_con_valores]:
                valor_unidad = [valor_unidad for nombre, valor_unidad in ingredientes_con_valores if nombre == nombreMateria][0]
                gramos_ajustados = float(cantidad) * float(valor_unidad)
                if nombreMateria in [nombre for nombre, porcentaje in ingredientes_con_cascara_porcentaje]:
                    porcentaje_cascara = [porcentaje for nombre, porcentaje in ingredientes_con_cascara_porcentaje if nombre == nombreMateria][0]
                    gramos_ajustados -= (float(cantidad) * float(valor_unidad) * float(porcentaje_cascara) / 100)
                    porcentaje = float((gramos_ajustados/float(valor_unidad*50))*100)
                    if nombreMateria == "Leche" or nombreMateria == "Vainilla":
                            idMedida = 3
                    elif nombreMateria == "Huevo":
                        idMedida = 1
                    else:
                        idMedida = 2

                    materia_prima_existente = MateriaPrima.query.get(id_materiaPrima)

                    if materia_prima_existente:
                        materia_prima_existente.nombreMateria = nombreMateria
                        materia_prima_existente.precioCompra = precio
                        materia_prima_existente.cantidad = cantidad
                        materia_prima_existente.idMedida = idMedida
                        materia_prima_existente.idProveedor = proveedor_id

                        try:
                            db.session.commit()
                            flash("Materia prima actualizada correctamente.")
                        except Exception as e:
                            db.session.rollback()
                            flash("Error al actualizar la materia prima en la base de datos: " + str(e))
                    else:
                        flash("La materia prima con el ID proporcionado no existe en la base de datos.")

                    detalle_existente = Detalle_materia_prima.query.filter_by(idMateriaPrima=id_materiaPrima).first()

                    if detalle_existente:

                        detalle_existente.fechaCompra = fechaCom
                        detalle_existente.fechaVencimiento = fechaVen
                        detalle_existente.cantidadExistentes = gramos_ajustados
                        detalle_existente.porcentaje = porcentaje

                        try:
                            db.session.commit()
                            flash("Detalle de materia prima actualizado correctamente.")
                        except Exception as e:
                            db.session.rollback()
                            flash("Error al actualizar el detalle de materia prima en la base de datos: " + str(e))
                    else:
                        flash("El detalle de materia prima correspondiente al ID proporcionado no existe en la base de datos.")
                else:
                    gramos_ajustados = valor_unidad * (float(cantidad))
                    if nombreMateria == "Leche" or nombreMateria == "Vainilla":
                            idMedida = 3
                    elif nombreMateria == "Huevo":
                        idMedida = 1
                    else:
                        idMedida = 2

                    materia_prima_existente = MateriaPrima.query.get(id_materiaPrima)

                    if materia_prima_existente:
                        materia_prima_existente.nombreMateria = nombreMateria
                        materia_prima_existente.precioCompra = precio
                        materia_prima_existente.cantidad = cantidad
                        materia_prima_existente.idMedida = idMedida
                        materia_prima_existente.idProveedor = proveedor_id

                        try:
                            db.session.commit()
                            flash("Materia prima actualizada correctamente.")
                        except Exception as e:
                            db.session.rollback()
                            flash("Error al actualizar la materia prima en la base de datos: " + str(e))
                    else:
                        flash("La materia prima con el ID proporcionado no existe en la base de datos.")

                    detalle_existente = Detalle_materia_prima.query.filter_by(idMateriaPrima=id_materiaPrima).first()

                    if detalle_existente:

                        detalle_existente.fechaCompra = fechaCom
                        detalle_existente.fechaVencimiento = fechaVen
                        detalle_existente.cantidadExistentes = gramos_ajustados
                        detalle_existente.porcentaje = porcentaje

                        try:
                            db.session.commit()
                            flash("Detalle de materia prima actualizado correctamente.")
                        except Exception as e:
                            db.session.rollback()
                            flash("Error al actualizar el detalle de materia prima en la base de datos: " + str(e))
                    else:
                        flash("El detalle de materia prima correspondiente al ID proporcionado no existe en la base de datos.")
            else:
                flash("Este ingrediente no puede ser comprado por unidad.")
        else:
            flash("Tipo de compra no válido.")

        
    return redirect(url_for('inventario'))

@app.route("/eliminar_inventario", methods=['POST'])
@login_required
def eliminar_inventario():
    id_materia_prima = int(request.form.get("idMateriaPrima"))
    id_detalle_prima = int(request.form.get("idDetallePrima"))
    cantidad_merma = float(request.form.get("cantidadE"))
    detalle_prima = Detalle_materia_prima.query.get(id_detalle_prima)
    
    if detalle_prima:
        detalle_prima.estatus = 0
        db.session.commit()

        nueva_merma = merma_inventario(
                        cantidadMerma=cantidad_merma,
                        idMateriaPrima=id_materia_prima,
                        idDetalle_materia_prima=id_materia_prima
                    )
        db.session.add(nueva_merma)
        db.session.commit()
        mensaje = "Materia prima y detalle eliminados correctamente."
        flash(mensaje)
    else:
        mensaje = "Materia prima o detalle no encontrados."
        flash(mensaje)
    
    return redirect(url_for('inventario'))

@app.route("/registrar_merma", methods=['POST'])
@login_required
def registrar_merma():
    id_detalle_prima = ""
    cantidad_merma = 0
    merma = forms.InventarioForm(request.form)
    if request.method == 'POST':
        #id_detalle_prima = int(request.form.get("idDetalle"))
        id_materia = int(request.form.get("idMateria"))
        cantidad_merma = float(merma.merma.data)

        detalle_prima = Detalle_materia_prima.query.get(id_materia)

        if detalle_prima:
            cantidad_existente = detalle_prima.cantidadExistentes
            if cantidad_existente is not None and cantidad_existente >= cantidad_merma:
                detalle_prima.cantidadExistentes -= cantidad_merma
                db.session.commit()

                nueva_merma = merma_inventario(
                        cantidadMerma=cantidad_merma,
                        idMateriaPrima=id_materia,
                        idDetalle_materia_prima=id_materia
                    )
                db.session.add(nueva_merma)
                db.session.commit()

                mensaje = "Merma registrada correctamente."
                flash(mensaje)
            elif cantidad_existente is not None:
                mensaje = "La cantidad de merma supera la cantidad existente."
                flash(mensaje)
            else:
                mensaje = "Cantidad existente no disponible para el detalle de materia prima."
                flash(mensaje)
        else:
            mensaje = "Detalle de materia prima no encontrado."
            flash(mensaje)

    return redirect(url_for('inventario'))

# Fin del Modulo de Materia Prima

@app.route('/punto_de_venta')
@login_required
@ventas_required
def punto_de_venta():
    productos = Producto.query.all()
    detalles_producto = Detalle_producto.query.filter_by(estatus=1).order_by(Detalle_producto.fechaVencimiento.desc()).all()
    return render_template('venta.html', productos=productos, detalles_producto=detalles_producto)

@app.route('/pv_galleta_ticket', methods=['POST'])
@login_required
def pv_galleta():
    datos = request.form.get('datos2')
    user = request.form.get('user')
    empresa = 'TentaCrisp'
    datosPy = json.loads(datos)
    cantidad = 0

    total = calcular_total(datosPy)
    fecha = datetime.now()

    nueva_venta = Venta(total=total, fechaVenta=fecha)
    db.session.add(nueva_venta)
    db.session.commit()
    

    for detalle in datosPy:
        cantidad = detalle['piezas'] + detalle['caja700g'] + detalle['caja1kg'] + detalle['gramos']
        id_producto = detalle['id']
        nuevo_detalle = DetalleVenta(
            cantidad=cantidad,
            subtotal=detalle['subtotal'],
            idProducto=detalle['id'],
            idVenta=nueva_venta.idVenta,
            idMedida=1
        )
        db.session.add(nuevo_detalle)
        descontar_cantidad_producto(id_producto, cantidad)

    db.session.commit()
    flash("Venta Generada,success")

    return generar_pdf(datosPy,fecha,user,empresa)

@app.route('/pv_galleta', methods=['POST'])
@login_required
def pv_galleta_Sin_Ticket():
    datos = request.form.get('datos')
    datosPy = json.loads(datos)
    cantidad = 0

    total = calcular_total(datosPy)
    fecha = datetime.now()

    nueva_venta = Venta(total=total, fechaVenta=fecha)
    db.session.add(nueva_venta)
    db.session.commit()
    

    for detalle in datosPy:
        cantidad = detalle['piezas'] + detalle['caja700g'] + detalle['caja1kg'] + detalle['gramos']
        id_producto = detalle['id']
        nuevo_detalle = DetalleVenta(
            cantidad=cantidad,
            subtotal=detalle['subtotal'],
            idProducto=detalle['id'],
            idVenta=nueva_venta.idVenta,
            idMedida=1
        )
        db.session.add(nuevo_detalle)
        descontar_cantidad_producto(id_producto, cantidad)

    db.session.commit()
    flash("Venta Generada,success")

    return redirect(url_for('punto_de_venta'))

def descontar_cantidad_producto(id_producto, cantidad):
    detalle_producto = Detalle_producto.query.filter_by(idProducto=id_producto).first()

    if detalle_producto:
        if detalle_producto.cantidadExistentes >= cantidad:
            detalle_producto.cantidadExistentes -= cantidad
            db.session.commit()
        else:
            flash("No hay suficiente producto en existencia", "error")
    else:
        flash("El producto no fue encontrado", "error")

def calcular_total(datos):
    total = 0
    for detalle in datos:
        total += detalle['subtotal']
    return total

def generar_pdf(datos, fecha_compra, comprador, empresa):
    datosPy = datos
    
    pdf_filename = "venta.pdf"
    c = canvas.Canvas(pdf_filename, pagesize=letter)

    logo_path = "static/img/Galletas-removebg-preview (1).png"
    c.drawImage(logo_path, 250, 220, width=100, height=100)
    # Agregar título
    c.setFont("Helvetica-Bold", 16)
    c.drawString(100, 670, "!Vuelva pronto¡")

    c.setFont("Helvetica", 12)
    c.drawString(100, 650, f"Fecha de compra: {fecha_compra}")
    c.drawString(100, 630, f"Lo atendio : {comprador}")
    c.setFillColorRGB(0.1, 0.3, 0.5)
    c.drawString(100, 610, empresa)

    # Agregar los datos como tabla centrada
    datos_tabla = [["Piezas", "Caja 700g", "Caja 1kg", "Gramos", "Subtotal"]]
    for detalle in datosPy:
        datos_tabla.append([
            detalle['piezas'],
            detalle['caja700g'],
            detalle['caja1kg'],
            detalle['gramos'],
            detalle['subtotal']
        ])
    
    tabla = Table(datos_tabla)
    tabla.setStyle(TableStyle([
        ('BACKGROUND', (0, 0), (-1, 0), colors.grey),
        ('TEXTCOLOR', (0, 0), (-1, 0), colors.whitesmoke),
        ('ALIGN', (0, 0), (-1, -1), 'CENTER'),
        ('FONTNAME', (0, 0), (-1, 0), 'Helvetica-Bold'),
        ('BOTTOMPADDING', (0, 0), (-1, 0), 12),
        ('BACKGROUND', (0, 1), (-1, -1), colors.beige),
        ('GRID', (0, 0), (-1, -1), 1, colors.black),
        ('INNERGRID', (0, 0), (-1, -1), 0.5, colors.black),
        ('VALIGN', (0, 0), (-1, -1), 'MIDDLE'),
    ]))

    width, height = letter
    tabla.wrapOn(c, width-100, height)
    tabla.drawOn(c, (width-tabla._width)/2, 400)

    total = sum(detalle['subtotal'] for detalle in datosPy)
    c.drawString(100, 100, f"Total: ${total}")

    c.save()

    response = make_response(send_file(pdf_filename, as_attachment=True))
    response.headers['Content-Disposition'] = 'attachment; filename=venta.pdf'
    return response

@app.route('/solicitud_lote',methods=['GET', 'POST'])
@login_required
@admin_required
def solicitud_lote():
    id_producto = request.form.get('idProducto-lote')
    cantidad_producto = request.form.get('cantidad-lotes')
    fecha = datetime.now()
    print ("id_producto " ,id_producto)
    print ("cantidad_producto ", cantidad_producto)
    print ("fecha" , fecha)

    nueva_solicitud = solicitudProduccion(
            cantidadProduccion=cantidad_producto,
            fechaSolicitud=fecha,
            idProducto=id_producto
        )
    db.session.add(nueva_solicitud)

    db.session.commit()
    flash("Solicitud Enviada")


    return redirect(url_for('punto_de_venta'))



@app.route('/logs')
@login_required
@admin_required
def logs():
    logs = LogsUser.query.all()

    return render_template('logs.html', logs=logs)

if __name__ == '__main__':
    csrf.init_app(app)
    db.init_app(app)
    with app.app_context():
        db.create_all()
        
    app.run(host='0.0.0.0')