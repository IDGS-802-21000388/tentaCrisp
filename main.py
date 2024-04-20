import forms, ssl, json, re, html2text, pandas as pd, os, matplotlib
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
from inventario.inventario import inventario_page
from inventario.inventario import inventario_page
from proveedor.proveedor import proveedor_page
from puntoVenta.puntoVenta import puntoVenta_page
matplotlib.use('Agg')

app = Flask(__name__)
app.register_blueprint(producir_page, url_prefix='/produccion')
app.register_blueprint(inventario_page)
app.register_blueprint(proveedor_page)
app.register_blueprint(puntoVenta_page)

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
        print("Contraseña",generate_password_hash(contrasenia))
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


# Fin del Modulo de Proveedores

# Inicio del Modulo de Materia Prima


# Fin del Modulo de Materia Prima

password_pattern = re.compile(r'^(?=.*[a-z])(?=.*[A-Z])(?=.*\d)(?=.*[@$!%*?&])[A-Za-z\d@$!%*?&]{8,}$')

@app.route('/usuarios', methods=['GET', 'POST'])
@login_required
@admin_required
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
@login_required
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
@login_required
def cambiar_estado_usuario(id_usuario):
    usuario = Usuario.query.get(id_usuario)
    if usuario:
        usuario.estatus = 0  # Cambiar el estado del usuario a inactivo
        db.session.commit()
        flash('Usuario eliminado correctamente', 'success')
    else:
        flash('Usuario no encontrado', 'error')

    return redirect(url_for('usuarios'))

@app.route('/compras', methods=['POST', 'GET'])
@login_required
@produccion_required
def mostrar_compras():
    form = forms.ComprasForm()

    if request.method == 'POST' and form.validate():
        tipo_busqueda = form.tipo_seleccion.data
        fecha_seleccionada = form.fecha.data
        compras, img_url = obtener_compras_y_grafica(tipo_busqueda, fecha_seleccionada)
        if not compras:
            flash("No hay compras para la fecha seleccionada.", "warning")
            return render_template('compras.html', form=form)
        return render_template('compras.html', form=form, compras=compras, img_url=img_url)

    compras, img_url = obtener_compras_y_grafica()
    if not compras:
        flash("No hay compras disponibles.", "warning")
        return render_template('compras.html', form=form)
    return render_template('compras.html', form=form, compras=compras, img_url=img_url)

def obtener_compras_y_grafica(tipo_busqueda=None, fecha_seleccionada=None):
    fecha_inicio, fecha_fin = calcular_rango_fechas(tipo_busqueda, fecha_seleccionada)

    compras = Compra.query.join(Detalle_materia_prima).filter(Detalle_materia_prima.fechaCompra.between(fecha_inicio, fecha_fin)).all()
    for compra in compras:
        compra.materia_prima = MateriaPrima.query.get(compra.idMateriaPrima)
        detalle = Detalle_materia_prima.query.filter_by(idDetalle_materia_prima=compra.idDetalle_materia_prima).first()
        if detalle:
            compra.fecha_compra = detalle.fechaCompra.strftime('%Y-%m-%d') if detalle.fechaCompra else None
            compra.fecha_vencimiento = detalle.fechaVencimiento.strftime('%Y-%m-%d') if detalle.fechaVencimiento else None
    
    # Obtener mermas de cada materia prima
    mermas = merma_inventario.query.all()
    mermas_dict = {}
    for merma in mermas:
        if merma.idMateriaPrima not in mermas_dict:
            mermas_dict[merma.idMateriaPrima] = merma.cantidadMerma
        else:
            mermas_dict[merma.idMateriaPrima] += merma.cantidadMerma

    data = []
    for compra in compras:
        nombre = compra.materia_prima.nombreMateria
        cantidad_comprada = compra.cantidadExistentes
        cantidad_merma = mermas_dict.get(compra.materia_prima.idMateriaPrima, 0)
        data.append([nombre, cantidad_comprada, cantidad_merma, compra.fecha_compra, compra.fecha_vencimiento])
    
    df = pd.DataFrame(data, columns=['Nombre', 'Compras', 'Merma', 'Fecha_Compra', 'Fecha_Vencimiento'])
    df = df.groupby('Nombre').sum().reset_index()

    if df.empty:
        return None, None  # Retorna None para compras y img_url si no hay datos

    plt = df.plot(x='Nombre', kind='bar', stacked=True, figsize=(10, 6), color=['#A67C52', '#E77F34'])
    plt.set_xlabel('Materia Prima')
    plt.set_ylabel('Cantidad')
    plt.set_title('Compras y Merma de Materia Prima')
    plt.legend()
    plt.grid(axis='y')

    for p in plt.patches:
        if p.get_height() > 0:
            plt.annotate(str(int(p.get_height())), (p.get_x() + p.get_width() / 2., p.get_height()), ha='center', va='bottom')
        else:
            plt.annotate(str(int(p.get_height())), (p.get_x() + p.get_width() / 2., p.get_height()), ha='center', va='top')

    fig = plt.get_figure()
    img_path = os.path.join(app.root_path, 'static', 'img', 'compras.png')
    fig.savefig(img_path)
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
@admin_required
@login_required
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
    
    if total_ventas is None:
        flash("No hay ventas registradas.", "warning")
    
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

        # Generar la gráfica utilizando Pandas
        ax = df_ventas_agrupado.plot(kind='bar', x='Producto', y='Subtotal', figsize=(10, 6), colormap=colormap)

        # Añadir líneas en el eje Y
        ax.grid(axis='y')

        # Etiquetar cada barra con su valor correspondiente
        for p in ax.patches:
            if p.get_height() > 0:
                ax.annotate(str(int(p.get_height())), (p.get_x() + p.get_width() / 2., p.get_height()), ha='center', va='bottom')
            else:
                ax.annotate(str(int(p.get_height())), (p.get_x() + p.get_width() / 2., p.get_height()), ha='center', va='top')

        ax.set_xlabel('Producto')  # Corregido
        ax.set_ylabel('$ Total Ventas')  # Corregido
        ax.set_title('Top 10 de Productos más Vendidos')  # Corregido
        ax.set_xticklabels(df_ventas_agrupado['Producto'], rotation=45, ha='right')  # Corregido
        plt.tight_layout()
        plt.savefig('static/top_10_productos_mas_vendidos.png')
        plt.close()

    return total_ventas, ventas_detalle, df_ventas_agrupado

@app.route('/ganancias', methods=['GET', 'POST'])
@login_required
@admin_required
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
    plt.pie([total_ventas, total_compras], labels=['Ventas\nCantidad: {}'.format(total_ventas), 'Gastos\nCantidad: {}'.format(total_compras)], startangle=140, counterclock=False, colors=['green', 'red'], wedgeprops=dict(width=0.4))
    plt.title('TentaCrisp S.A de CV\nEstado de resultados')

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
    # Paso 1: Calcular el total de compras de materia prima
    query_compras = db.session.query(func.sum(MateriaPrima.precioCompra))
    
    if fecha_inicio is not None and fecha_fin is not None:
        query_compras = query_compras.select_from(Detalle_materia_prima).join(MateriaPrima).filter(Detalle_materia_prima.fechaCompra.between(fecha_inicio, fecha_fin))
    else:
        query_compras = query_compras.select_from(MateriaPrima)
    
    total_compras_materia_prima = query_compras.scalar()

    if total_compras_materia_prima is None:
        total_compras_materia_prima = 0.0

    print("Total de compras de materia prima:", total_compras_materia_prima)

    # Paso 2: Calcular el total de merma de producto
    query_merma_producto = db.session.query(func.sum(Merma.cantidadMerma * Producto.precioVenta))
    
    if fecha_inicio is not None and fecha_fin is not None:
        query_merma_producto = query_merma_producto.join(Producto, Merma.idProducto == Producto.idProducto).filter(Merma.fechaMerma.between(fecha_inicio, fecha_fin))
    
    total_merma_producto = query_merma_producto.scalar()

    if total_merma_producto is None:
        total_merma_producto = 0.0

    print("Total de merma de producto:", total_merma_producto)

    # Paso 3: Calcular el total de merma de inventario
    total_merma_inventario = calcular_valor_total_mermaInventario(fecha_inicio, fecha_fin)
    
    print("Total de merma de inventario:", total_merma_inventario)
    
    total_precio_produccion= calcular_precio_produccion_galletas_vendidas(fecha_inicio, fecha_fin)
    
    print("Total de precio de produccion:", total_precio_produccion)

    # Paso 4: Sumar los totales de compras y merma
    total_compras = total_compras_materia_prima + total_merma_producto + total_merma_inventario + total_precio_produccion

    print("Total de compras con merma:", total_compras)

    return total_compras

def calcular_valor_total_mermaInventario(fecha_inicio=None, fecha_fin=None):
    # Paso 1: Obtener todas las merma de inventario dentro del rango de fechas
    merma = merma_inventario.query.filter(merma_inventario.fechaMerma.between(fecha_inicio, fecha_fin)).all()

    # Paso 2: Calcular la cantidad total de merma
    cantidad_total_merma = sum(m.cantidadMerma for m in merma)

    # Paso 3: Calcular el precio total de las compras de materia prima
    compras = Compra.query.join(Detalle_materia_prima).all()
    precio_total_compras = sum(MateriaPrima.query.filter_by(idMateriaPrima=compra.idMateriaPrima).first().precioCompra for compra in compras)

    # Paso 4: Calcular el precio por unidad de materia prima
    if precio_total_compras != 0:
        precio_por_unidad = precio_total_compras / sum(compra.cantidadExistentes for compra in compras)
    else:
        precio_por_unidad = 0.0

    # Paso 5: Calcular el valor total de la merma
    valor_total_merma = cantidad_total_merma * precio_por_unidad

    return valor_total_merma

def calcular_precio_produccion_galletas_vendidas(fecha_inicio=None, fecha_fin=None):

    # Filtrar las ventas por fecha
    ventas = Venta.query.filter(Venta.fechaVenta.between(fecha_inicio, fecha_fin)).all()

    # Inicializar el precio total de producción de las galletas vendidas
    precio_produccion_galletas_vendidas = 0.0

    # Iterar sobre cada venta para obtener los detalles de venta y calcular el precio total de producción
    for venta in ventas:
        detalles_venta = DetalleVenta.query.filter_by(idVenta=venta.idVenta).all()
        for detalle in detalles_venta:
            producto = Producto.query.get(detalle.idProducto)
            precio_produccion_galletas_vendidas += detalle.cantidad * producto.precioProduccion

    return precio_produccion_galletas_vendidas






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