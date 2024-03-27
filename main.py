from flask import Flask, request, render_template, flash, g, redirect, url_for, session, jsonify
from flask_wtf.csrf import CSRFProtect
from config import DevelopmentConfig
import forms, ssl, base64, json
from models import db, Usuario, MateriaPrima, Producto, Detalle_producto, Receta, Detalle_receta
from sqlalchemy import func, and_
from functools import wraps
from flask_cors import CORS
from flask_wtf.recaptcha import Recaptcha
from datetime import datetime, timedelta
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
        nombreUsuario = usuario_form.nombreUsuario.data
        contrasenia = usuario_form.contrasenia.data
        user = Usuario.query.filter_by(nombreUsuario=nombreUsuario).first()
        if user and check_password_hash(user.contrasenia, contrasenia):
            login_user(user)
            #flash('Inicio de sesión exitoso', 'success')
            user.dateLastToken = datetime.utcnow() - timedelta(hours=6)
            db.session.commit()
            return jsonify({'success': True, 'redirect': url_for('index')})
        else:
            #flash('Usuario o contraseña inválidos', 'error')
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

@app.route('/recetas', methods=['GET', 'POST'])
def recetas():
    getAllingredientes = getAllIngredientes()
    nueva_galleta_form = forms.NuevaGalletaForm()
    ingredientes = []
    productos = []

    productos_detalle = db.session.query(Producto, Detalle_producto).outerjoin(Detalle_producto, Producto.idProducto == Detalle_producto.idProducto).filter(and_(Producto.estatus == 1)).all()
    for producto, detalle in productos_detalle:
    # Verificar si el producto tiene un estado activo (estatus = 1)
        if producto.estatus == 1:
            ingredientes_asociados = db.session.query(MateriaPrima, Detalle_receta).join(Detalle_receta, MateriaPrima.idMateriaPrima == Detalle_receta.idMateriaPrima).filter(Detalle_receta.idReceta == detalle.idProducto).all()
            
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
                'cantidadExistentes': detalle.cantidadExistentes,
                'ingredientes': ingredientes_serializados_json
            }

            productos.append(producto_dict)

    #if len(productos) == 0:
    #    productos.append({})

    if request.method == 'POST' and nueva_galleta_form.validate():
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

        detalle_producto = Detalle_producto(fechaVencimiento=fechaCaducidad, cantidadExistentes=0, idProducto=nuevo_producto.idProducto)
        db.session.add(detalle_producto)
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
        return redirect(url_for('recetas'))

    return render_template('receta.html', form=nueva_galleta_form, ingredientes=getAllingredientes, productos=productos)

@app.route('/editar_producto', methods=['GET', 'POST'])
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

        detalle_producto = Detalle_producto.query.filter_by(idProducto=id_producto).first()
        detalle_producto.cantidadExistentes = cantidad_existentes

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
def eliminar_producto():
    id_producto = None
    if request.method == 'POST':
        for key, value in request.form.items():
            if key.startswith('id_producto_'):
                id_producto = value        
        producto = Producto.query.get(id_producto)

        if producto:
            producto.estatus = False 
            db.session.commit()

            return redirect(url_for('recetas'))
        else:
            return 'No se encontró ningún producto con el ID proporcionado'
    else:
        return 'No se recibió una solicitud POST'

def getAllIngredientes():
    ingredientes = MateriaPrima.query.all()
    return ingredientes

if __name__ == '__main__':
    csrf.init_app(app)
    db.init_app(app)
    with app.app_context():
        db.create_all()
        
    app.run()