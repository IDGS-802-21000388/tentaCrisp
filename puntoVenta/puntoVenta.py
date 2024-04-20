from models import db,Producto, Detalle_producto,Venta, DetalleVenta,Detalle_producto,solicitudProduccion
from flask import request, render_template, flash, redirect, url_for, Blueprint,make_response, send_file
from functools import wraps
from flask_login import login_required, current_user
import json
from datetime import datetime
from reportlab.lib.pagesizes import letter
from reportlab.pdfgen import canvas
from reportlab.platypus import Table, TableStyle
from reportlab.lib import colors

puntoVenta_page = Blueprint('puntoVenta', __name__,
                          static_folder='static',
                          template_folder='templates'
                          )

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

@puntoVenta_page.route('/punto_de_venta')
@login_required
@ventas_required
def punto_de_venta():
    productos = Producto.query.all()
    detalles_producto = Detalle_producto.query.filter_by(estatus=1).order_by(Detalle_producto.fechaVencimiento.desc()).all()
    return render_template('venta.html', productos=productos, detalles_producto=detalles_producto)

@puntoVenta_page.route('/pv_galleta_ticket', methods=['POST'])
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

@puntoVenta_page.route('/pv_galleta', methods=['POST'])
@login_required
def pv_galleta_Sin_Ticket():
    datos = request.form.get('datos')
    datosPy = json.loads(datos)
    cantidad = 0
    print(datosPy)

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
        resultado = descontar_cantidad_producto(id_producto, cantidad)

    if resultado:
        db.session.commit()
        flash('Venta Generada','success')
    else:
        flash('No hay suficiente producto en existencia', 'error')
        return redirect(url_for('puntoVenta.punto_de_venta'))

    return redirect(url_for('puntoVenta.punto_de_venta'))

def descontar_cantidad_producto(id_producto, cantidad):
    detalle_producto = Detalle_producto.query.filter_by(idProducto=id_producto).first()

    if detalle_producto:
        if detalle_producto.cantidadExistentes >= cantidad:
            detalle_producto.cantidadExistentes -= cantidad
            db.session.commit()
            return True
        else:
            return False
    else:
        return False

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

@puntoVenta_page.route('/solicitud_lote',methods=['GET', 'POST'])
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
    flash('Solicitud Enviada','success')


    return redirect(url_for('puntoVenta.punto_de_venta'))
