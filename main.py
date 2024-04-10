from flask import Flask, request, render_template, flash, g, redirect, url_for, session, jsonify
from flask_wtf.csrf import CSRFProtect
from config import DevelopmentConfig
import forms, ssl, base64, json, re
from models import db, Usuario, MateriaPrima, Proveedor, Producto, Detalle_producto, Receta, Detalle_receta, Detalle_materia_prima, Medida, mermaInventario ,LogsUser, Venta, DetalleVenta
import forms, ssl, base64, json, re, html2text
from sqlalchemy import func , and_
from functools import wraps
from flask_cors import CORS
from flask_wtf.recaptcha import Recaptcha
from datetime import datetime ,timedelta, timezone
from flask_login import current_user, LoginManager, login_user, logout_user, login_required, login_manager
from werkzeug.security import generate_password_hash, check_password_hash
from sqlalchemy.orm import Session
ssl._create_default_https_context = ssl._create_unverified_context
from collections import defaultdict
from matplotlib import pyplot as plt
import os
from flask import render_template, send_from_directory
import matplotlib.pyplot as plt
from io import BytesIO
import base64
import pandas as pd
import matplotlib
matplotlib.use('Agg')
import numpy as np
from matplotlib.colors import ListedColormap


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

@app.route('/prueba')
def prueba():
    return render_template("layout2.html")

@app.route('/', methods=['GET', 'POST'])
def login():
    usuario_form = forms.LoginForm(request.form)
    
    if request.method == 'POST' and usuario_form.validate():
        fecha_hora_actual = datetime.now()
        bloqueado_hasta = session.get('bloqueado_hasta')
        bloqueado_hasta = datetime.fromisoformat(bloqueado_hasta) if bloqueado_hasta else None
        fecha_hora_actual = fecha_hora_actual.replace(microsecond=0)

        if bloqueado_hasta:
            bloqueado_hasta = bloqueado_hasta.replace(microsecond=0)

        if bloqueado_hasta and (fecha_hora_actual) < bloqueado_hasta:
            return redirect(url_for('login'))
        else:
            nombreUsuario = str(html2text.html2text(usuario_form.nombreUsuario.data)).strip()
            contrasenia = str(html2text.html2text(usuario_form.contrasenia.data)).strip()
            print("Nombre Usuario",nombreUsuario ,"Contraseña",contrasenia)
            print("Contraseña",generate_password_hash(contrasenia))
            user = Usuario.query.filter_by(nombreUsuario=nombreUsuario).first()
            if user and check_password_hash(user.contrasenia, contrasenia): 
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
                session.pop('intentos_fallidos', None)
                return jsonify({'success': True, 'redirect': url_for('index')})
            else:
                session['intentos_fallidos'] = session.get('intentos_fallidos', 0) + 1
                if session['intentos_fallidos'] >= 3:
                    session['bloqueado_hasta'] = (fecha_hora_actual + timedelta(minutes=1)).isoformat()
                    flash('Tu cuenta ha sido bloqueada temporalmente debido a múltiples intentos fallidos. Inténtalo de nuevo más tarde.', 'error')
                log = LogsUser(
                    procedimiento=f'Se intento Iniciar Sesión con las credenciales usuario:{nombreUsuario} y contraseña:{contrasenia} ',
                    lastDate=fecha_hora_actual,
                    idUsuario=0
                )
                db.session.add(log)
                db.session.commit()
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
        print("Nombre Materia",nombreMateria)
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
                        flash("Kilos ajustados Bulto" , gramos_ajustados)
                        porcentaje = float((gramos_ajustados / (float(valor_unidad) * 50)) * 100)
                        if nombreMateria in ingredientes_liquidos:
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
                        except Exception as e:
                            db.session.rollback()
                            flash("Error al agregar el detalle de materia prima a la base de datos: " + str(e))
                    else:
                        gramos_ajustados = valor_unidad * (float(cantidad) * float(campoKilosBulto))

                        if nombreMateria in ingredientes_liquidos:
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

                        if nombreMateria in ingredientes_liquidos:
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
                        except Exception as e:
                            db.session.rollback()
                            flash("Error al agregar el detalle de materia prima a la base de datos: " + str(e))

                    else:
                        gramos_ajustados = valor_unidad * (float(cantidad) * float(valor_unidad))
                        if nombreMateria in ingredientes_liquidos:
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
                        if nombreMateria in ingredientes_liquidos:
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
                        except Exception as e:
                            db.session.rollback()
                            flash("Error al agregar el detalle de materia prima a la base de datos: " + str(e))
                else:
                    gramos_ajustados = valor_unidad * (float(cantidad) * float(valor_unidad))
                    if nombreMateria in ingredientes_liquidos:
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
                    except Exception as e:
                        db.session.rollback()
                        flash("Error al agregar el detalle de materia prima a la base de datos: " + str(e))
            else:
                
                flash("Este ingrediente no puede ser comprado por unidad.")
        else:
            flash("Tipo de compra no válido.")
    

    materias_primas = MateriaPrima.query.all()
    detalle_primas = Detalle_materia_prima.query.all()
    print("Detalle Prima", detalle_primas)
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
        print("Nombre Materia",nombreMateria)
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
                        flash("Kilos ajustados" , kilos_ajustados)
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
                        flash("Kilos ajustados" , kilos_ajustados)
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
def eliminar_inventario():
    id_detalle_prima = int(request.form.get("idDetallePrima"))
    detalle_prima = Detalle_materia_prima.query.get(id_detalle_prima)
    
    if detalle_prima:
        detalle_prima.estatus = 0
        db.session.commit()
        mensaje = "Materia prima y detalle eliminados correctamente."
        flash(mensaje)
    else:
        mensaje = "Materia prima o detalle no encontrados."
        flash(mensaje)
    
    return redirect(url_for('proveedor'))

@app.route("/registrar_merma", methods=['POST'])
def registrar_merma():
    id_detalle_prima = ""
    cantidad_merma = 0
    merma = forms.InventarioForm(request.form)
    if request.method == 'POST':
        id_detalle_prima = int(request.form.get("idDetalle"))
        cantidad_merma = float(merma.cantidad.data)

        detalle_prima = Detalle_materia_prima.query.get(id_detalle_prima)

        if detalle_prima:
            cantidad_existente = detalle_prima.cantidadExistentes
            print("Cantidad existente: ", cantidad_existente)
            if cantidad_existente is not None and cantidad_existente >= cantidad_merma:
                detalle_prima.cantidadExistentes -= cantidad_merma
                db.session.commit()

                nueva_merma = mermaInventario(
                        cantidadMerma=cantidad_merma,
                        idMateriaPrima=id_detalle_prima
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

@app.route('/recetas', methods=['GET', 'POST'])
@login_required
def recetas():
    getAllingredientes = getAllIngredientes()
    nueva_galleta_form = forms.NuevaGalletaForm()
    ingredientes = []
    productos = []
    productos_detalle = db.session.query(Producto).all()

    for producto in productos_detalle:
        fecha_vencimiento_producto = ''
        cantidad_existentes_producto = ''
            
        ingredientes_asociados = db.session.query(MateriaPrima, Detalle_receta).join(Detalle_receta, MateriaPrima.idMateriaPrima == Detalle_receta.idMateriaPrima).filter(Detalle_receta.idReceta == producto.idProducto).all()
            
        ingredientes_serializados = []
        for ingrediente, detalle_receta in ingredientes_asociados:
            ingrediente_dict = {
                'id': ingrediente.idMateriaPrima,
                'nombre': ingrediente.nombreMateria,
                'cantidad': detalle_receta.porcion
            }
            ingredientes_serializados.append(ingrediente_dict)
            
        ingredientes_serializados_json = json.dumps(ingredientes_serializados)

        producto_dict = {
            'idProducto': producto.idProducto,
            'nombreProducto': producto.nombreProducto,
            'precioProduccion': producto.precioProduccion,
            'precioVenta': producto.precioVenta,
            'fotografia': producto.fotografia,
            'estatus': producto.estatus,
            'cantidadExistentes': cantidad_existentes_producto,
            'fechaVencimiento': fecha_vencimiento_producto,
            'ingredientes': ingredientes_serializados_json
        }

        productos.append(producto_dict)

    #if len(productos) == 0:
    #    productos.append({})

    if request.method == 'POST' :
        nombre_galleta = nueva_galleta_form.nombre_galleta.data
        precio_produccion = nueva_galleta_form.precio_produccion.data
        precio_venta = nueva_galleta_form.precio_venta.data
        fechaCaducidad = nueva_galleta_form.fechaCaducidad.data

        if 'fotografia' in request.files:
            fotografia_archivo = request.files['fotografia']            
            imagen_bytes = fotografia_archivo.read()            
            imagen_base64 = base64.b64encode(imagen_bytes).decode("utf-8")

        for key, value in request.form.items():
            if key.startswith('ingredientes_'):
                id_ingrediente = key.split('_')[1]
                valor_ingrediente = value
                ingredientes.append({'id':id_ingrediente, 'cantidad':valor_ingrediente})

        nuevo_producto = Producto(nombreProducto=nombre_galleta, precioVenta=precio_venta, precioProduccion=precio_produccion, idMedida=2, fotografia=imagen_base64)
        db.session.add(nuevo_producto)
        db.session.commit()

        #detalle_producto = Detalle_producto(fechaVencimiento=fechaCaducidad, cantidadExistentes=0, idProducto=nuevo_producto.idProducto)
        #db.session.add(detalle_producto)
        nueva_receta = Receta(idMedida=1, idProducto=nuevo_producto.idProducto)
        db.session.add(nueva_receta)
        db.session.commit()

        for key, value in request.form.items():
            if key.startswith('ingredientes_'):
                id_ingrediente = key.split('_')[1]
                valor_ingrediente = value

                detalle_receta = Detalle_receta(porcion=valor_ingrediente, idMateriaPrima=id_ingrediente, idReceta=nueva_receta.idReceta)
                db.session.add(detalle_receta)

        db.session.commit()
        flash('La receta ha sido agregada correctamente!', 'success')
        return redirect(url_for('recetas'))

    return render_template('receta.html', form=nueva_galleta_form, ingredientes=getAllingredientes, productos=productos)

@app.route('/editar_producto', methods=['GET', 'POST'])
@login_required
def editar_producto():
    getAllingredientes = getAllIngredientes()
    nueva_galleta_form = forms.NuevaGalletaForm()
    productos = []
    detalle_productos = Detalle_producto.query.all()
    fotografia_base64 = None
    id_producto = None
    if request.method == 'POST':
        id_producto = request.form.get('product')
        nombre_producto = request.form.get('nombre_producto')
        cantidad_existentes = request.form.get('cantidad_existentes')
        precio_produccion = request.form.get('precio_produccion')
        precio_venta = request.form.get('precio_venta')
        fotografia = request.files['fotografia_editar']
        
        producto = Producto.query.get(id_producto)
        producto.nombreProducto = nombre_producto
        producto.precioProduccion = precio_produccion
        producto.precioVenta = precio_venta

        if fotografia:
            fotografia = request.files['fotografia_editar']
            fotografia_base64 = base64.b64encode(fotografia.read()).decode('utf-8')
            producto.fotografia = fotografia_base64

        #detalle_producto = Detalle_producto.query.filter_by(idProducto=id_producto).first()
        #detalle_producto.cantidadExistentes = cantidad_existentes

        ingredientes_presentes = []

        for key, value in request.form.items():
            if key.startswith('ingredienteseditar_'):
                id_ingrediente = key.split('_')[-1]
                cantidad_ingrediente = value
                ingredientes_presentes.append(id_ingrediente)
                
                receta = Receta.query.filter_by(idProducto=id_producto).first()
                detalle_receta = Detalle_receta.query.filter_by(idReceta=receta.idReceta, idMateriaPrima=id_ingrediente).first()
                
                if detalle_receta:
                    detalle_receta.porcion = cantidad_ingrediente
                else:
                    nuevo_detalle_receta = Detalle_receta(porcion=cantidad_ingrediente, idMateriaPrima=id_ingrediente, idReceta=id_producto)
                    db.session.add(nuevo_detalle_receta)

        receta = Receta.query.filter_by(idProducto=id_producto).first()
        detalles_receta_actuales = Detalle_receta.query.filter(and_(Detalle_receta.idReceta == receta.idReceta, ~Detalle_receta.idMateriaPrima.in_(ingredientes_presentes))).all()

        for detalle_receta_actual in detalles_receta_actuales:
            db.session.delete(detalle_receta_actual)

        db.session.commit()
        
        flash('El producto ha sido editado!', 'success')
        return redirect(url_for('recetas'))
    
    for producto, detalle in zip(Producto.query.all(), detalle_productos):
        producto_dict = {
            'idProducto': producto.idProducto,
            'nombreProducto': producto.nombreProducto,
            'precioProduccion': producto.precioProduccion,
            'precioVenta': producto.precioVenta,
            'cantidadExistentes': detalle.cantidadExistentes
        }
        productos.append(producto_dict)
    
    return render_template('receta.html', form=nueva_galleta_form, ingredientes=getAllingredientes, productos=productos)

@app.route('/eliminar_logica_producto', methods=['POST'])
@login_required
def eliminar_producto():
    id_producto = None
    fecha_vencimiento = request.form.get('fecha_vencimiento')
    accion = request.form.get('accion')
    if request.method == 'POST':
        for key, value in request.form.items():
            if key.startswith('id_producto_'):
                id_producto = value        
        producto = Producto.query.get(id_producto)
        if accion == 'eliminar':
            if producto:
                producto.estatus = False
                db.session.commit()
                flash('¡El producto ha sido eliminado lógicamente!', 'success')
                return redirect(url_for('recetas'))
            else:
                flash('No se encontró ningún producto con el ID proporcionado', 'error')
                return 'No se encontró ningún producto con el ID proporcionado'
        elif accion =='activar':
            if producto:
                producto.estatus = True
                db.session.commit()
                flash('¡El producto ha sido activado lógicamente!', 'success')
                return redirect(url_for('recetas'))
            else:
                flash('No se encontró ningún producto con el ID proporcionado', 'error')
                return 'No se encontró ningún producto con el ID proporcionado'
    else:
        flash('No se recibió una solicitud POST', 'error')
        return 'No se recibió una solicitud POST'

@app.route('/producir', methods=['POST'])
@login_required
def producir():
    if request.method == 'POST':
        cantidadProduccion = 40
        cantidadMerma = int(request.form.get('cantidadMerma')) if request.form.get('cantidadMerma') else 0
        idProducto = int(request.form.get('productoSeleccionado')) if request.form.get('productoSeleccionado') else 0
        fechaVencimiento = request.form.get('fechaVencimiento') if request.form.get('fechaVencimiento') else 0
        print('fechaVencimiento')
        print(fechaVencimiento)
        if idProducto == 0 or fechaVencimiento == 0:
            flash('Por favor, completa todos los campos correctamente', 'error')
            return redirect(url_for('productos'))
        detalle_producto = Detalle_producto(
            fechaVencimiento=fechaVencimiento,
            cantidadExistentes=cantidadProduccion - cantidadMerma,
            idProducto=idProducto
        )
        db.session.add(detalle_producto)
        db.session.commit()

        receta = Receta.query.filter_by(idProducto=idProducto).first()
        if receta:
            detalles_receta = Detalle_receta.query.filter_by(idReceta=receta.idReceta).all()
            for detalle in detalles_receta:
                materia_prima = MateriaPrima.query.get(detalle.idMateriaPrima)
                cantidad_necesaria = detalle.porcion
                detalle_materia_prima = Detalle_materia_prima.query.filter_by(idMateriaPrima=materia_prima.idMateriaPrima, estatus=1).filter(Detalle_materia_prima.cantidadExistentes > 0).first()
                if detalle_materia_prima:
                    detalle_materia_prima.cantidadExistentes -= cantidad_necesaria
                    db.session.commit()
                else:
                    flash(f'No se encontró ingriendientes en existencia para {materia_prima.nombreMateria}', 'error')
                    return redirect(url_for('productos'))
            flash('La galletas se han horneado!', 'success')
            return redirect(url_for('productos'))
    else:
        flash('No se recibió una solicitud POST', 'error')
        return 'No se recibió una solicitud POST'

@app.route('/del_act_logica_produccion', methods=['POST'])
@login_required
def eliminar_logica_produccion():
    id_producto = None
    fecha_vencimiento = request.form.get('fecha_vencimiento1')
    accion = request.form.get('accion')

    for key, value in request.form.items():
            if key.startswith('id_producto_'):
                id_producto = value     
    if accion == 'eliminar':   
        detalle_producto = Detalle_producto.query.filter_by(idProducto=id_producto, fechaVencimiento=fecha_vencimiento).first()
        if detalle_producto:
            detalle_producto.estatus = False
            db.session.commit()
            
            flash('¡El detalle del producto ha sido eliminado lógicamente!', 'success')
    elif accion == 'activar':
        detalle_producto = Detalle_producto.query.filter_by(idProducto=id_producto, fechaVencimiento=fecha_vencimiento).first()
        if detalle_producto:
            detalle_producto.estatus = True
            db.session.commit()
            
            flash('¡El detalle del producto ha sido activado lógicamente!', 'success')
    else:
        flash('No se encontró ningún detalle de producto con el ID y fecha proporcionados', 'error')

    return redirect(url_for('productos'))

@app.route('/productos', methods=['GET', 'POST'])
@login_required
def productos():
    productos = []
    products_activos = []
    producto_dict = {}

    productos_activos = Producto.query.filter_by(estatus=1).all()
    for producto in productos_activos:
        producto_dict = {
            'idProducto': producto.idProducto,
            'nombreProducto': producto.nombreProducto,
            'precioProduccion': producto.precioProduccion,
            'precioVenta': producto.precioVenta,
            'fotografia': producto.fotografia,
        }
    if len(producto_dict) > 0:
        products_activos.append(producto_dict)

    productos_detalle = db.session.query(Producto, Detalle_producto).outerjoin(Detalle_producto, Producto.idProducto == Detalle_producto.idProducto).filter(Producto.estatus == 1).all()
    productos_detalle_filtrados = [(producto, detalle) for producto, detalle in productos_detalle if detalle is not None]

    for producto, detalle in productos_detalle_filtrados:
        if detalle is not None:
            fecha_vencimiento_producto = detalle.fechaVencimiento.strftime("%Y-%m-%d %H:%M:%S") if detalle.fechaVencimiento else ''
            cantidad_existentes_producto = detalle.cantidadExistentes if detalle.cantidadExistentes else ''
            detalle_estatus = detalle.estatus

        ingredientes_asociados = db.session.query(MateriaPrima, Detalle_receta).join(Detalle_receta, MateriaPrima.idMateriaPrima == Detalle_receta.idMateriaPrima).filter(Detalle_receta.idReceta == producto.idProducto).all()
        
        ingredientes_serializados = []
        for ingrediente, detalle_receta in ingredientes_asociados:
            ingrediente_dict = {
                'id': ingrediente.idMateriaPrima,
                'nombre': ingrediente.nombreMateria,
                'cantidad': detalle_receta.porcion
            }
            ingredientes_serializados.append(ingrediente_dict)

        ingredientes_serializados_json = json.dumps(ingredientes_serializados)
        
        producto_dict = {
            'idProducto': producto.idProducto,
            'nombreProducto': producto.nombreProducto,
            'precioProduccion': producto.precioProduccion,
            'precioVenta': producto.precioVenta,
            'fotografia': producto.fotografia,
            'detalle_estatus': detalle_estatus,
            'cantidadExistentes': cantidad_existentes_producto,
            'fechaVencimiento': fecha_vencimiento_producto,
            'ingredientes': ingredientes_serializados_json
        }

        productos.append(producto_dict)

    return render_template('productos.html', productos=productos, products=products_activos)

def getAllIngredientes():
    ingredientes = MateriaPrima.query.all()
    return ingredientes

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
    
        if contrasenia != usuario.contrasenia:
            usuario.contrasenia = generate_password_hash(contrasenia)
        
            if not password_pattern.match(contrasenia):
                flash('La contraseña debe contener al menos una mayúscula, una minúscula, un número y un carácter especial.', 'error')
                return redirect(url_for('usuarios'))

            if contrasenia in lista_contraseñas_no_seguras:
                flash('La contraseña no puede ser una contraseña por defecto o previamente utilizada.', 'error')
                return redirect(url_for('usuarios'))
               
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

@app.route('/compras', methods=['GET', 'POST'])
def mostrar_compras():
    form = forms.ComprasForm()  # Crear una instancia del formulario de compras

    if request.method == 'POST' and form.validate():
        tipo_busqueda = form.tipo_seleccion.data
        fecha_seleccionada = form.fecha.data
        compras, img_url = obtener_compras_y_grafica(tipo_busqueda, fecha_seleccionada)
        return render_template('compras.html', form=form, compras=compras, img_url=img_url)

    # Si la solicitud es GET o el formulario no es válido, mostrar todas las compras
    compras, img_url = obtener_compras_y_grafica()
    return render_template('compras.html', form=form, compras=compras, img_url=img_url)


def obtener_compras_y_grafica(tipo_busqueda=None, fecha_seleccionada=None):
    # Obtener el rango de fechas según el tipo de búsqueda
    fecha_inicio, fecha_fin = calcular_rango_fechas(tipo_busqueda, fecha_seleccionada)

    # Filtrar las compras por el rango de fechas
    compras = Detalle_materia_prima.query.filter(Detalle_materia_prima.fechaCompra.between(fecha_inicio, fecha_fin)).all()

    # Obtener instancias de MateriaPrima correspondientes a cada compra
    for compra in compras:
        compra.materia_prima = MateriaPrima.query.get(compra.idMateriaPrima)
    
    # Obtener mermas de cada materia prima dentro del rango de fechas
    mermas = mermaInventario.query.all()
    mermas_dict = {}
    for merma in mermas:
        if merma.idMateriaPrima not in mermas_dict:
            mermas_dict[merma.idMateriaPrima] = merma.cantidadMerma
        else:
            mermas_dict[merma.idMateriaPrima] += merma.cantidadMerma

    # Crear un DataFrame de Pandas con los datos de compras y mermas
    data = []
    for compra in compras:
        nombre = compra.materia_prima.nombreMateria
        cantidad_comprada = compra.cantidadExistentes
        cantidad_merma = mermas_dict.get(compra.materia_prima.idMateriaPrima, 0)
        data.append([nombre, cantidad_comprada, cantidad_merma])
    
    df = pd.DataFrame(data, columns=['Nombre', 'Compras', 'Merma'])
    
    # Consolidar las compras y mermas para cada materia prima
    df = df.groupby('Nombre').sum().reset_index()

    # Generar la gráfica utilizando Pandas
    plt = df.plot(x='Nombre', kind='bar', stacked=True, figsize=(10, 6))
    plt.set_xlabel('Materia Prima')
    plt.set_ylabel('Cantidad')
    plt.set_title('Compras y Merma de Materia Prima')
    plt.legend()

    # Obtener el objeto de figura (Figure)
    fig = plt.get_figure()

    # Guardar la gráfica como un archivo de imagen
    img_path = os.path.join(app.root_path, 'static', 'img', 'compras.png')
    fig.savefig(img_path)

    # Obtener la ubicación de la imagen para pasarla a la plantilla HTML
    img_url = url_for('static', filename='img/compras.png')
    
    return compras, img_url

def calcular_rango_fechas(tipo_busqueda=None, fecha_seleccionada=None):
    if tipo_busqueda == 'dia':
        # Si se selecciona la búsqueda por día, el rango de fechas será la fecha seleccionada
        fecha_inicio = fecha_seleccionada
        fecha_fin = fecha_seleccionada + timedelta(days=1)
    elif tipo_busqueda == 'semana':
        # Si se selecciona la búsqueda por semana, se calcula la semana a la que pertenece la fecha seleccionada
        fecha_inicio_semana = fecha_seleccionada - timedelta(days=fecha_seleccionada.weekday())
        fecha_fin_semana = fecha_inicio_semana + timedelta(days=7)
        fecha_inicio = fecha_inicio_semana
        fecha_fin = fecha_fin_semana
    elif tipo_busqueda == 'mes':
        # Si se selecciona la búsqueda por mes, se calcula el primer y último día del mes de la fecha seleccionada
        primer_dia_mes = fecha_seleccionada.replace(day=1)
        ultimo_dia_mes = primer_dia_mes.replace(day=1, month=primer_dia_mes.month % 12 + 1) - timedelta(days=1)
        fecha_inicio = primer_dia_mes
        fecha_fin = ultimo_dia_mes
    else:
        # Si se selecciona la búsqueda por todos, no se aplica ningún filtro de fecha
        fecha_inicio = datetime.min
        fecha_fin = datetime.max
    
    return fecha_inicio, fecha_fin

def calcular_total_compras():
    # Obtener todas las compras de materia prima
    compras = Detalle_materia_prima.query.all()

    # Inicializar el total de compras
    total_compras = 0.0

    # Calcular el total de compras sumando el producto del precio de compra y la cantidad de cada compra
    for compra in compras:
        materia_prima = MateriaPrima.query.get(compra.idMateriaPrima)
        if materia_prima:
            total_compras += materia_prima.precioCompra * compra.cantidadExistentes

    return total_compras



@app.route('/ventas', methods=['GET', 'POST'])
def ventas():
    form = forms.VentasForm()  # Crear una instancia del formulario de ventas

    if request.method == 'POST' and form.validate():
        tipo_seleccion = form.tipo_seleccion.data
        fecha_seleccionada = form.fecha.data

        total_ventas, ventas_detalle, df_ventas_agrupado = calcular_total_tipoventas(tipo_seleccion, fecha_seleccionada)

        if total_ventas is None:
            flash("No hay ventas para la fecha seleccionada.", "warning")
            return render_template('dashboard_ventas.html', form=form)

        return render_template('dashboard_ventas.html', form=form, ventas=total_ventas, ventas_detalle=ventas_detalle, df_ventas_agrupado=df_ventas_agrupado)

    # Si la solicitud es GET, mostrar todas las ventas
    total_ventas, ventas_detalle, df_ventas_agrupado = calcular_total_tipoventas()
    return render_template('dashboard_ventas.html', form=form, ventas=total_ventas, ventas_detalle=ventas_detalle, df_ventas_agrupado=df_ventas_agrupado)


def calcular_total_tipoventas(tipo_seleccion=None, fecha_seleccionada=None):
    total_ventas = 0.0
    ventas_detalle = []

    if tipo_seleccion == 'dia':
        ventas_productos = db.session.query(
            DetalleVenta.idProducto,
            func.sum(DetalleVenta.cantidad).label('cantidad_total'),
            func.sum(DetalleVenta.subtotal).label('subtotal_total'),
            Venta.fechaVenta,
        ).join(Venta).filter(
            Venta.idVenta == DetalleVenta.idVenta,
            func.date(Venta.fechaVenta) == func.date(fecha_seleccionada)
        ).group_by(DetalleVenta.idProducto, Venta.fechaVenta).all()

        for producto, cantidad, subtotal, fecha_venta in ventas_productos:
            nombre_producto = Producto.query.get(producto).nombreProducto
            ventas_detalle.append((nombre_producto, cantidad, subtotal, fecha_venta))
            total_ventas += subtotal

    elif tipo_seleccion == 'semana':
        fecha_inicio_semana = fecha_seleccionada - timedelta(days=fecha_seleccionada.weekday())
        fecha_fin_semana = fecha_inicio_semana + timedelta(days=6)
        ventas_productos = db.session.query(
            DetalleVenta.idProducto,
            func.sum(DetalleVenta.cantidad).label('cantidad_total'),
            func.sum(DetalleVenta.subtotal).label('subtotal_total'),
            Venta.fechaVenta,
        ).join(Venta).filter(
            Venta.idVenta == DetalleVenta.idVenta,
            func.date(Venta.fechaVenta) >= func.date(fecha_inicio_semana),
            func.date(Venta.fechaVenta) <= func.date(fecha_fin_semana)
        ).group_by(DetalleVenta.idProducto, Venta.fechaVenta).all()

        for producto, cantidad, subtotal, fecha_venta in ventas_productos:
            nombre_producto = Producto.query.get(producto).nombreProducto
            ventas_detalle.append((nombre_producto, cantidad, subtotal, fecha_venta))
            total_ventas += subtotal

    elif tipo_seleccion == 'mes':
        primer_dia_mes = fecha_seleccionada.replace(day=1)
        ultimo_dia_mes = primer_dia_mes.replace(day=1, month=primer_dia_mes.month % 12 + 1) - timedelta(days=1)
        ventas_productos = db.session.query(
            DetalleVenta.idProducto,
            func.sum(DetalleVenta.cantidad).label('cantidad_total'),
            func.sum(DetalleVenta.subtotal).label('subtotal_total'),
            Venta.fechaVenta,
        ).join(Venta).filter(
            Venta.idVenta == DetalleVenta.idVenta,
            func.date(Venta.fechaVenta) >= func.date(primer_dia_mes),
            func.date(Venta.fechaVenta) <= func.date(ultimo_dia_mes)
        ).group_by(DetalleVenta.idProducto, Venta.fechaVenta).all()

        for producto, cantidad, subtotal, fecha_venta in ventas_productos:
            nombre_producto = Producto.query.get(producto).nombreProducto
            ventas_detalle.append((nombre_producto, cantidad, subtotal, fecha_venta))
            total_ventas += subtotal
            
    elif tipo_seleccion == 'todos':
        ventas_productos = db.session.query(
            DetalleVenta.idProducto,
            func.sum(DetalleVenta.cantidad).label('cantidad_total'),
            func.sum(DetalleVenta.subtotal).label('subtotal_total'),
            Venta.fechaVenta,
        ).join(Venta).group_by(DetalleVenta.idProducto, Venta.fechaVenta).all()

        for producto, cantidad, subtotal, fecha_venta in ventas_productos:
            nombre_producto = Producto.query.get(producto).nombreProducto
            ventas_detalle.append((nombre_producto, cantidad, subtotal, fecha_venta))
            total_ventas += subtotal

    else:  # Si tipo_seleccion es None, obtén todas las ventas
        ventas_productos = db.session.query(
            DetalleVenta.idProducto,
            func.sum(DetalleVenta.cantidad).label('cantidad_total'),
            func.sum(DetalleVenta.subtotal).label('subtotal_total'),
            Venta.fechaVenta,
        ).join(Venta).group_by(DetalleVenta.idProducto, Venta.fechaVenta).all()

        for producto, cantidad, subtotal, fecha_venta in ventas_productos:
            nombre_producto = Producto.query.get(producto).nombreProducto
            ventas_detalle.append((nombre_producto, cantidad, subtotal, fecha_venta))
            total_ventas += subtotal

    df_ventas_agrupado = None
    if ventas_detalle:
        df_ventas = pd.DataFrame(ventas_detalle, columns=['Producto', 'Cantidad', 'Subtotal', 'Fecha'])
        df_ventas_agrupado = df_ventas.groupby('Producto').agg({'Subtotal': 'sum', 'Cantidad': 'first'}).reset_index()
        df_ventas_agrupado = df_ventas_agrupado.sort_values(by='Subtotal', ascending=False).head(10)

        base_color = '#dfb98b'  # Nuevo color base
        num_colors = len(df_ventas_agrupado)
        color_palette = [base_color]

        for i in range(num_colors - 1):
            new_color = plt.cm.colors.hex2color(plt.cm.colors.rgb2hex(plt.cm.colors.colorConverter.to_rgb(base_color)) + (0.1, 0.1, 0.1))
            color_palette.append(new_color)

        colormap = ListedColormap(color_palette)

        df_ventas_agrupado.plot(kind='bar', x='Producto', y='Subtotal', figsize=(10, 6), colormap=colormap)
        plt.xlabel('Producto')
        plt.ylabel('$ Total Ventas')
        plt.title('Top 10 de Productos más Vendidos')
        plt.xticks(rotation=45, ha='right')
        plt.tight_layout()
        plt.savefig('static/top_10_productos_mas_vendidos.png')
        plt.close()

    return total_ventas, ventas_detalle, df_ventas_agrupado

@app.route('/ganancias', methods=['GET', 'POST'])
def ganancias():
    form = forms.GananciasForm()
    if request.method == 'POST' and form.validate():
        tipo_seleccion = form.tipo_seleccion.data
        fecha_seleccionada = form.fecha.data

        ganancias_result = calcular_ganancias(tipo_seleccion, fecha_seleccionada)

        if ganancias_result is None:
            flash("No hay datos de ganancias para la fecha seleccionada.", "warning")
            return render_template('ganancias.html', form=form)

        # Verificar la longitud de ganancias_result y desempaquetar en consecuencia
        if len(ganancias_result) == 3:
            total_ventas, total_compras, img_url = ganancias_result
            ganancias = None  # No hay datos de ganancias en este caso
        else:
            total_ventas, total_compras, ganancias, img_url = ganancias_result

        return render_template('ganancias.html', form=form, total_ventas=total_ventas, total_compras=total_compras, ganancias=ganancias, img_url=img_url)

    ganancias_result = calcular_ganancias()  # Si la solicitud es GET, mostrar todas las ganancias
    if ganancias_result is None:
        flash("No hay datos de ganancias para la fecha seleccionada.", "warning")
        return render_template('ganancias.html', form=form)

    # Verificar la longitud de ganancias_result y desempaquetar en consecuencia
    if len(ganancias_result) == 3:
        total_ventas, total_compras, img_url = ganancias_result
        ganancias = None  # No hay datos de ganancias en este caso
    else:
        total_ventas, total_compras, ganancias, img_url = ganancias_result

    return render_template('ganancias.html', form=form, total_ventas=total_ventas, total_compras=total_compras, ganancias=ganancias, img_url=img_url)


def calcular_ganancias(tipo_seleccion=None, fecha_seleccionada=None):
    # Calcular el rango de fechas según el tipo de selección
    fecha_inicio, fecha_fin = calcular_rango_fechas(tipo_seleccion, fecha_seleccionada)

    # Filtrar las ventas y compras por el rango de fechas
    total_ventas = calcular_total_ventas(fecha_inicio, fecha_fin)
    total_compras = calcular_total_compras(fecha_inicio, fecha_fin)
    if total_ventas == 0 and total_compras == 0:
        flash("No hay datos disponibles para la fecha seleccionada.", "warning")
        return None, None, None, None
    # Calcular las ganancias
    ganancias = total_ventas - total_compras

    # Definir el color de las ganancias dependiendo de si son positivas o negativas
    if total_ventas is None or total_compras is None:
        flash("No hay datos disponibles para la fecha seleccionada.", "warning")
        return None, None, None, None

    # Crear la gráfica de dona con los segmentos de ventas y compras
    plt.figure(figsize=(10, 6))  # Ajustar el tamaño de la figura
    plt.pie([total_ventas, total_compras], labels=['Total Ventas\nCantidad: {}'.format(total_ventas), 'Total Compras\nCantidad: {}'.format(total_compras)], startangle=140, counterclock=False, colors=['green', 'red'], wedgeprops=dict(width=0.4))
    plt.title('Total de Ventas y Compras')

    # Agregar un círculo en el centro para hacerla una dona
    centre_circle = plt.Circle((0, 0), 0.70, fc='white')
    fig = plt.gcf()
    fig.gca().add_artist(centre_circle)

    # Guardar la gráfica como una imagen en la carpeta static
    img_path = 'static/total_ventas_compras_dona.png'
    plt.savefig(img_path)
    plt.close()

    # Obtener la ubicación de la imagen para pasarla a la plantilla HTML
    img_url = url_for('static', filename='total_ventas_compras_dona.png')

    return total_ventas, total_compras, ganancias, img_url

def calcular_rango_fechas(tipo_seleccion=None, fecha_seleccionada=None):
    if tipo_seleccion == 'dia':
        # Si se selecciona la búsqueda por día, el rango de fechas será la fecha seleccionada
        fecha_inicio = fecha_seleccionada
        fecha_fin = fecha_seleccionada + timedelta(days=1)
    elif tipo_seleccion == 'semana':
        # Si se selecciona la búsqueda por semana, se calcula la semana a la que pertenece la fecha seleccionada
        fecha_inicio_semana = fecha_seleccionada - timedelta(days=fecha_seleccionada.weekday())
        fecha_fin_semana = fecha_inicio_semana + timedelta(days=7)
        fecha_inicio = fecha_inicio_semana
        fecha_fin = fecha_fin_semana
    elif tipo_seleccion == 'mes':
        # Si se selecciona la búsqueda por mes, se calcula el primer y último día del mes de la fecha seleccionada
        primer_dia_mes = fecha_seleccionada.replace(day=1)
        ultimo_dia_mes = primer_dia_mes.replace(day=1, month=primer_dia_mes.month % 12 + 1) - timedelta(days=1)
        fecha_inicio = primer_dia_mes
        fecha_fin = ultimo_dia_mes
    else:
        # Si se selecciona la búsqueda por todos, no se aplica ningún filtro de fecha
        fecha_inicio = datetime.min
        fecha_fin = datetime.max

    return fecha_inicio, fecha_fin

def calcular_total_ventas(fecha_inicio=None, fecha_fin=None):
    if fecha_inicio is not None and fecha_fin is not None:
        total_ventas = db.session.query(func.sum(Venta.total)).filter(Venta.fechaVenta.between(fecha_inicio, fecha_fin)).scalar()
    else:
        total_ventas = db.session.query(func.sum(Venta.total)).scalar()

    return total_ventas if total_ventas is not None else 0.0

def calcular_total_compras(fecha_inicio=None, fecha_fin=None):
    if fecha_inicio is not None and fecha_fin is not None:
        total_compras = db.session.query(func.sum(Detalle_materia_prima.cantidadExistentes * MateriaPrima.precioCompra)).join(MateriaPrima).filter(Detalle_materia_prima.fechaCompra.between(fecha_inicio, fecha_fin)).scalar()
    else:
        total_compras = db.session.query(func.sum(Detalle_materia_prima.cantidadExistentes * MateriaPrima.precioCompra)).join(MateriaPrima).scalar()

    return total_compras if total_compras is not None else 0.0





if __name__ == '__main__':
    csrf.init_app(app)
    db.init_app(app)
    with app.app_context():
        db.create_all()
        
    app.run()