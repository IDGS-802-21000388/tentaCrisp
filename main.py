from flask import Flask, request, render_template, flash, g, redirect, url_for, session, jsonify
from flask_wtf.csrf import CSRFProtect
from config import DevelopmentConfig
import forms, ssl, base64, json, re
from models import db, Usuario, MateriaPrima, Producto, Detalle_producto, Receta, Detalle_receta
from sqlalchemy import func, and_
from functools import wraps
from flask_cors import CORS
from flask_wtf.recaptcha import Recaptcha
from datetime import datetime, timedelta
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
def editar_producto():
    getAllingredientes = getAllIngredientes()
    nueva_galleta_form = forms.NuevaGalletaForm()
    productos = []
    detalle_productos = Detalle_producto.query.all()
    fotografia_base64 = None
    id_producto = None
    print(request.form)
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
def eliminar_producto():
    id_producto = None
    fecha_vencimiento = request.form.get('fecha_vencimiento')
    accion = request.form.get('accion')
    print(request.form)
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
def producir():
    if request.method == 'POST':
        cantidadProduccion = 40
        cantidadMerma = int(request.form.get('cantidadMerma')) if request.form.get('cantidadMerma') else 0
        idProducto = int(request.form.get('productoSeleccionado'))
        fechaVencimiento = request.form.get('fechaVencimiento')

        detalle_producto = Detalle_producto(
            fechaVencimiento=fechaVencimiento,
            cantidadExistentes=cantidadProduccion - cantidadMerma,
            idProducto=idProducto
        )
        db.session.add(detalle_producto)
        db.session.commit()

        return redirect(url_for('productos'))
    else:
        flash('No se recibió una solicitud POST', 'error')
        return 'No se recibió una solicitud POST'

@app.route('/del_act_logica_produccion', methods=['POST'])
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
def productos():
    productos = []
    products_activos = []
    
    productos_activos = Producto.query.filter_by(estatus=1).all()
    for producto in productos_activos:
        producto_dict = {
            'idProducto': producto.idProducto,
            'nombreProducto': producto.nombreProducto,
            'precioProduccion': producto.precioProduccion,
            'precioVenta': producto.precioVenta,
            'fotografia': producto.fotografia,
        }
    products_activos.append(producto_dict)

    productos_detalle = db.session.query(Producto, Detalle_producto).outerjoin(Detalle_producto, Producto.idProducto == Detalle_producto.idProducto).filter(Producto.estatus == 1).all()

    for producto, detalle in productos_detalle:
        if detalle is not None:
            fecha_vencimiento_producto = detalle.fechaVencimiento.strftime("%Y-%m-%d %H:%M:%S") if detalle.fechaVencimiento else ''
            cantidad_existentes_producto = detalle.cantidadExistentes if detalle.cantidadExistentes else ''
            detalle_estatus = detalle.estatus
        else:
            detalle = Detalle_producto(fechaVencimiento='', cantidadExistentes='')
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
            'detalle_estatus': detalle_estatus,
            'cantidadExistentes': cantidad_existentes_producto,
            'fechaVencimiento': fecha_vencimiento_producto,
            'ingredientes': ingredientes_serializados_json
        }

        productos.append(producto_dict)
    with open('productos.json', 'w') as json_file:
        json.dump(productos, json_file, indent=4)

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