import forms, base64, json
from datetime import datetime
from sqlalchemy import and_
from functools import wraps
from flask_login import current_user, login_required
from flask import request, render_template, flash, redirect, url_for, Blueprint
from models import db, MateriaPrima, Producto, Detalle_producto, Receta, Detalle_receta, Medida, Detalle_producto, solicitudProduccion, Merma, Detalle_materia_prima

producir_page = Blueprint('produccion', __name__, 
                          static_folder='static', 
                          template_folder='templates'
                          )

def produccion_required(f):
    @wraps(f)
    def decorated_function(*args, **kwargs):
        if current_user.rol != 'Administrador':
            if current_user.rol != 'Produccion':
                flash('No tienes permisos', 'warning')
                return redirect(url_for('index'))
            return f(*args, **kwargs)
        return f(*args, **kwargs)
    return decorated_function

@producir_page.route('/recetas', methods=['GET', 'POST'])
@login_required
@produccion_required
def recetas():
    getAllingredientes = getAllIngredientes()
    nueva_galleta_form = forms.NuevaGalletaForm()
    ingredientes = []
    productos = []
    productos_detalle = db.session.query(Producto).all()

    for producto in productos_detalle:
        fecha_vencimiento_producto = ''
        cantidad_existentes_producto = ''
            
        ingredientes_asociados = db.session.query(MateriaPrima, Detalle_receta, Medida).join(Detalle_receta, MateriaPrima.idMateriaPrima == Detalle_receta.idMateriaPrima).join(Medida, MateriaPrima.idMedida == Medida.idMedida).filter(Detalle_receta.idReceta == producto.idProducto).all()
        ingredientes_serializados = []
        for ingrediente, detalle_receta, medida in ingredientes_asociados:
            ingrediente_dict = {
                'id': ingrediente.idMateriaPrima,
                'nombre': ingrediente.nombreMateria,
                'cantidad': detalle_receta.porcion,
                'medida': medida.tipoMedida
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
        return redirect(url_for('produccion.recetas'))

    return render_template('receta.html', form=nueva_galleta_form, ingredientes=getAllingredientes, productos=productos)

@producir_page.route('/editar_producto', methods=['GET', 'POST'])
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
        return redirect(url_for('produccion.recetas'))
    
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

@producir_page.route('/eliminar_logica_producto', methods=['POST'])
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
                return redirect(url_for('produccion.recetas'))
            else:
                flash('No se encontró ningún producto con el ID proporcionado', 'error')
                return 'No se encontró ningún producto con el ID proporcionado'
        elif accion =='activar':
            if producto:
                producto.estatus = True
                db.session.commit()
                flash('¡El producto ha sido activado lógicamente!', 'success')
                return redirect(url_for('produccion.recetas'))
            else:
                flash('No se encontró ningún producto con el ID proporcionado', 'error')
                return 'No se encontró ningún producto con el ID proporcionado'
    else:
        flash('No se recibió una solicitud POST', 'error')
        return 'No se recibió una solicitud POST'

def getAllIngredientes():
    ingredientes = db.session.query(
        MateriaPrima.idMateriaPrima,
        MateriaPrima.nombreMateria,
        MateriaPrima.precioCompra,
        MateriaPrima.cantidad,
        Medida.tipoMedida
    ).join(
        Medida, MateriaPrima.idMedida == Medida.idMedida
    ).all()

    ingredientes_json = []
    for ingrediente in ingredientes:
        ingrediente_dict = {
            'idMateriaPrima': ingrediente.idMateriaPrima,
            'nombreMateria': ingrediente.nombreMateria,
            'precioCompra': ingrediente.precioCompra,
            'cantidad': ingrediente.cantidad,
            'tipoMedida': ingrediente.tipoMedida
        }
        ingredientes_json.append(ingrediente_dict)
    return ingredientes

# produccion

@producir_page.route('/producir', methods=['POST'])
@login_required
@produccion_required
def producir():
    if request.method == 'POST':
        id_solicitud = request.form.get('productoSeleccionado')
        if id_solicitud:
            solicitud = solicitudProduccion.query.get(id_solicitud)
            if solicitud:
                receta = Receta.query.filter_by(idProducto=solicitud.idProducto).first()
                if receta:
                    detalles_receta = Detalle_receta.query.filter_by(idReceta=receta.idReceta).all()
                    cantidad_necesaria_total = 0

                    # Calcular la cantidad total necesaria de todas las materias primas
                    for detalle in detalles_receta:
                        materia_prima = MateriaPrima.query.get(detalle.idMateriaPrima)
                        cantidad_necesaria = detalle.porcion * solicitud.cantidadProduccion
                        cantidad_necesaria_total += cantidad_necesaria

                    # Verificar si hay suficiente cantidad de materias primas disponibles para producir
                    cantidad_restante = cantidad_necesaria_total
                    for detalle in detalles_receta:
                        materia_prima = MateriaPrima.query.get(detalle.idMateriaPrima)
                        cantidad_necesaria = detalle.porcion * solicitud.cantidadProduccion

                        # Filtrar los detalles de materia prima disponibles que pueden cubrir la cantidad necesaria
                        detalles_materia_prima = Detalle_materia_prima.query.filter_by(idMateriaPrima=materia_prima.idMateriaPrima, estatus=1).filter(Detalle_materia_prima.cantidadExistentes >= cantidad_necesaria).all()

                        if detalles_materia_prima:
                            for detalle_mp in detalles_materia_prima:
                                if detalle_mp.cantidadExistentes >= cantidad_restante:
                                    # Si el detalle de materia prima actual puede cubrir la cantidad restante, comenzar la producción
                                    solicitud.estatus = 2
                                    db.session.commit()
                                    flash('Comenzó con la producción de la galleta', 'success')
                                    return redirect(url_for('produccion.productos'))
                            # Si el detalle de materia prima actual no puede cubrir la cantidad restante, actualizar la cantidad restante
                            cantidad_restante -= detalle_mp.cantidadExistentes
                    flash('No hay suficiente cantidad de materias primas en existencia para producir la cantidad necesaria de galletas', 'error')
                    return redirect(url_for('produccion.productos'))
                else:
                    flash('No se encontró la receta asociada al producto', 'error')
                    return redirect(url_for('produccion.productos'))
            else:
                return 'La solicitud de producción no existe', 404
        else:
            return 'ID de solicitud no proporcionado en el formulario', 400

@producir_page.route('/terminar_produccion', methods=['POST'])
@login_required
@produccion_required
def terminar_produccion():
    if request.method == 'POST':
        cantidadProduccion = 40
        cantidadMerma = int(request.form.get('cantidadMerma')) if request.form.get('cantidadMerma') else 0
        idProducto = int(request.form.get('txtIdProductoProd')) if request.form.get('txtIdProductoProd') else 0
        fechaVencimiento = request.form.get('fechaVencimiento') if request.form.get('fechaVencimiento') else 0
        cantidadProducirLotes = request.form.get('cantidadProducirProd') if request.form.get('cantidadProducirProd') else 0
        cantidadProduccion = int(cantidadProducirLotes) * 40

        if idProducto == 0 or fechaVencimiento == 0 or cantidadMerma<0:
            flash('Por favor, completa todos los campos correctamente', 'error')
            return redirect(url_for('produccion.productos'))
        
        if cantidadMerma > int(cantidadProduccion):
            flash('La cantidad de merma no puede ser mayor que la cantidad total producida', 'error')
            return redirect(url_for('produccion.productos'))
        
        detalle_producto = Detalle_producto(
            fechaVencimiento=fechaVencimiento,
            cantidadExistentes= int(cantidadProduccion) - cantidadMerma,
            idProducto=idProducto
        )
        db.session.add(detalle_producto)
        db.session.commit()

        if cantidadMerma != 0:
            merma = Merma(
                cantidadMerma=cantidadMerma,
                fechaMerma=datetime.now(),
                idProducto=idProducto,
                descripcion="Galletas que fueron merma durante el proceso de producción.",
                idDetalle_producto=detalle_producto.idDetalle_producto
            )
            db.session.add(merma)

        receta = Receta.query.filter_by(idProducto=idProducto).first()

        if receta:
            detalles_receta = Detalle_receta.query.filter_by(idReceta=receta.idReceta).all()
            for detalle in detalles_receta:
                materia_prima = MateriaPrima.query.get(detalle.idMateriaPrima)
                cantidad_necesaria = detalle.porcion * int(cantidadProducirLotes)
                detalles_materia_prima = Detalle_materia_prima.query.filter_by(idMateriaPrima=materia_prima.idMateriaPrima, estatus=1).filter(Detalle_materia_prima.cantidadExistentes > 0).all()

                for detalle_materia_prima in detalles_materia_prima:
                    cantidad_restante = detalle_materia_prima.cantidadExistentes - cantidad_necesaria

                    if cantidad_restante >= 0:
                        detalle_materia_prima.cantidadExistentes = cantidad_restante
                        cantidad_necesaria = 0
                    else:
                        cantidad_necesaria -= detalle_materia_prima.cantidadExistentes
                        detalle_materia_prima.cantidadExistentes = 0

                    if cantidad_necesaria <= 0:
                        break

                if cantidad_necesaria > 0:
                    flash(f'No hay suficiente cantidad de {materia_prima.nombreMateria} en existencia', 'error')
                    return redirect(url_for('produccion.productos'))

            flash('La galletas se han horneado!', 'success')
            id_solicitud = request.form.get('productoSeleccionadoProd')

            if id_solicitud:
                solicitud = solicitudProduccion.query.get(id_solicitud)
                if solicitud:
                    solicitud.estatus = 3
                    db.session.commit()

            return redirect(url_for('produccion.productos'))
    else:
        flash('No se recibió una solicitud POST', 'error')
        return 'No se recibió una solicitud POST'

@producir_page.route('/del_act_logica_produccion', methods=['POST'])
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
            merma = Merma(
                cantidadMerma=detalle_producto.cantidadExistentes,
                fechaMerma=datetime.now(),
                descripcion='Galletas vencidas o por vencer',
                idProducto=detalle_producto.idProducto,
                idDetalle_producto=detalle_producto.idDetalle_producto
            )
            db.session.add(merma)
            db.session.commit()

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

    return redirect(url_for('produccion.productos'))

@producir_page.route('/productos', methods=['GET', 'POST'])
@login_required
@produccion_required
def productos():
    productos = []
    products = []

    solicitudes = solicitudProduccion.query.filter(solicitudProduccion.estatus.in_([1, 2])).all()
    for solicitud in solicitudes:
        product = Producto.query.filter_by(idProducto=solicitud.idProducto).first()
        
        if product:
            products.append({
                'idSolicitud': solicitud.idSolicitud,
                'idProducto': product.idProducto,
                'nombreProducto': product.nombreProducto,
                'cantidadProduccion': solicitud.cantidadProduccion,
                'precioVenta': product.precioVenta,
                'precioProduccion': product.precioProduccion,
                'idMedida': product.idMedida,
                'fotografia': product.fotografia,
                'estatus': solicitud.estatus
            }) 

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

    return render_template('productos.html', productos=productos, products=products)

