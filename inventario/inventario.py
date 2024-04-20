from flask import request, render_template, flash, redirect, url_for, Blueprint
import forms
from flask_login import login_required, current_user
from functools import wraps
from datetime import datetime
from collections import defaultdict
from models import db, MateriaPrima, Proveedor, Medida,Detalle_materia_prima,merma_inventario, Compra

inventario_page = Blueprint('inventario', __name__, 
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

@inventario_page.route("/inventario", methods=['GET', 'POST'])
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
            ("Azucar", 1000),  # 1 kilogramo de azúcar
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
            ("Azucar moreno", 1000),  # 1 kilogramo de azúcar moreno
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
                            flash('Materia Prima agregada correctamente.', 'success')
                        except Exception as e:
                            flash('Error al agregar la materia prima a la base de datos', 'error')
                        
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
                            except Exception as e:
                                db.session.rollback()
                        except Exception as e:
                            db.session.rollback()
                        
                        
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
                            flash('Materia Prima agregada correctamente.', 'success')
                        except Exception as e:
                            flash('Error al agregar la materia prima a la base de datos', 'error')
                        
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
                            except Exception as e:
                                db.session.rollback()
                        except Exception as e:
                            db.session.rollback()
                else:
                    flash('Este ingrediente no puede ser encontrado.', 'error')
            else:
                flash('Este ingrediente no puede ser comprado en bulto.', 'error')
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
                            flash('Materia Prima agregada correctamente.', 'success')
                        except Exception as e:
                            flash('Error al agregar la materia prima a la base de datos', 'error')
                        
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
                            except Exception as e:
                                db.session.rollback()
                        except Exception as e:
                            db.session.rollback() 
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
                            flash('Materia Prima agregada correctamente.', 'success')
                        except Exception as e:
                            flash('Error al agregar la materia prima a la base de datos','error')
                        
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
                            except Exception as e:
                                db.session.rollback()
                        except Exception as e:
                            db.session.rollback()      
                else:
                    flash('Este ingrediente no puede ser encontrado.', 'error')
            else:
                flash('Este ingrediente no puede ser comprado por caja.', 'error')
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
                            flash('Materia Prima agregada correctamente.', 'success')
                        except Exception as e:
                            flash('Error al agregar la materia prima a la base de datos', 'error')
                        
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
                            except Exception as e:
                                db.session.rollback()
                        except Exception as e:
                            db.session.rollback()    
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
                        flash('Materia Prima agregada correctamente.', 'success')
                    except Exception as e:
                        flash('Error al agregar la materia prima a la base de datos:', 'error')
                    
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
                        except Exception as e:
                            db.session.rollback()
                    except Exception as e:
                        db.session.rollback()        
            else:
                
                flash('Este ingrediente no puede ser comprado por unidad.', 'error')
        else:
            flash('Tipo de compra no válido.', 'error')
    

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

@inventario_page.route('/editar_inventario', methods=['POST'])
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
            ("Azucar", 1000),  # 1 kilogramo de azúcar
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
            ("Azucar moreno", 1000),  # 1 kilogramo de azúcar moreno
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
                                flash('Materia prima actualizada correctamente.', 'success')
                            except Exception as e:
                                db.session.rollback()
                                flash('Error al actualizar la materia prima en la base de datos', 'error')
                        else:
                            flash('La materia prima proporcionado no existe en la base de datos.', 'success')

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
                        else:
                            print("El detalle de materia prima correspondiente al ID proporcionado no existe en la base de datos.")
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
                                flash('Materia prima actualizada correctamente.', 'success')
                            except Exception as e:
                                db.session.rollback()
                        else:
                            flash('La materia prima proporcionado no existe en la base de datos.','error')

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
                        else:
                            print("El detalle de materia prima correspondiente al ID proporcionado no existe en la base de datos.")
                else:
                    flash("Este ingrediente no puede ser encontrado.")
            else:
                flash('Este ingrediente no puede ser comprado en bulto.','error')
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
                                flash('Materia prima actualizada correctamente.','success')
                            except Exception as e:
                                db.session.rollback()
                                flash('Error al actualizar la materia prima en la base de datos: ','error')
                        else:
                            flash('La materia prima proporcionado no existe en la base de datos.','error')

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
                        else:
                            print('El detalle de materia prima proporcionado no existe en la base de datos.', 'error')
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
                                flash('Materia prima actualizada correctamente.', 'success')
                            except Exception as e:
                                db.session.rollback()
                                flash('Error al actualizar la materia prima en la base de datos ','error')
                        else:
                            flash('La materia prima con el ID proporcionado no existe en la base de datos.','error')

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
                        else:
                            print('El detalle de materia prima proporcionado no existe en la base de datos.', 'error')
                else:
                    flash('Este ingrediente no puede ser encontrado.', 'error')
            else:
                flash('Este ingrediente no puede ser comprado por caja.', 'error')
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
                            flash('Materia prima actualizada correctamente.', 'success')
                        except Exception as e:
                            db.session.rollback()
                            flash('Error al actualizar la materia prima en la base de datos ', 'error')
                    else:
                        flash('La materia prima con el ID proporcionado no existe en la base de datos.', 'error')

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
                    else:
                        print("El detalle de materia prima correspondiente al ID proporcionado no existe en la base de datos.")
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
                            flash('Materia prima actualizada correctamente.', 'success')
                        except Exception as e:
                            db.session.rollback()
                            flash('Error al actualizar la materia prima en la base de datos: ', 'error')
                    else:
                        print("La materia prima con el ID proporcionado no existe en la base de datos.")

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
                    else:
                        print("El detalle de materia prima correspondiente al ID proporcionado no existe en la base de datos.")
            else:
                flash('Este ingrediente no puede ser comprado por unidad.', 'error')
        else:
            flash('Tipo de compra no válido.', 'error')

        
    return redirect(url_for('inventario.inventario'))

@inventario_page.route("/eliminar_inventario", methods=['POST'])
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
        flash('Materia prima eliminados correctamente.' , 'success')
    else:
        flash('Materia prima o detalle no encontrados.', 'error')
    
    return redirect(url_for('inventario.inventario'))

@inventario_page.route("/registrar_merma", methods=['POST'])
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

                flash('Merma registrada correctamente.', 'success')
            elif cantidad_existente is not None:
                flash('La cantidad de merma supera la cantidad existente.', 'error')
            else:
                flash('Cantidad existente no disponible para el detalle de materia prima.', 'error')
        else:
            flash('Detalle de materia prima no encontrado.', 'error')

    return redirect(url_for('inventario.inventario'))