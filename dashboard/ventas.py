from flask import request, render_template, flash, redirect, url_for, Blueprint, current_app
import forms, ssl,ast as pd
from models import db, MateriaPrima, Producto, Detalle_materia_prima,  Venta, DetalleVenta, Detalle_materia_prima, Merma, Compra, merma_inventario
from sqlalchemy import func
from datetime import datetime ,timedelta
from flask_login import current_user, login_required
import matplotlib.pyplot as plt
from matplotlib import pyplot as plt
from matplotlib.colors import ListedColormap
import matplotlib.pyplot as plt
from matplotlib.colors import hex2color, rgb2hex, colorConverter
import numpy as np
import pandas as pd
from functools import wraps

ventas_page = Blueprint('ventas', __name__, 
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

@ventas_page.route('/ventas', methods=['GET', 'POST'])
@admin_required
@login_required
def ventas():
    form = forms.VentasForm()  

    if request.method == 'POST' and form.validate():
        tipo_seleccion = form.tipo_seleccion.data
        fecha_seleccionada = form.fecha.data

        total_ventas, ventas_detalle, df_ventas_agrupado = calcular_total_tipoventas(tipo_seleccion, fecha_seleccionada)

        if total_ventas is None:
            flash("No hay ventas para la fecha seleccionada.", "warning")
            return render_template('dashboard_ventas.html', form=form)

        return render_template('dashboard_ventas.html', form=form, ventas=total_ventas, ventas_detalle=ventas_detalle, df_ventas_agrupado=df_ventas_agrupado)

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

    else: 
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
        
        base_color = '#dfb98b'  
        num_colors = len(df_ventas_agrupado)
        color_palette = [base_color]

        rgb_hex = rgb2hex(colorConverter.to_rgb(base_color))
        rgb_tuple = np.array(hex2color(rgb_hex))
        new_color = hex2color(rgb_tuple + np.array((0.1, 0.1, 0.1)))
     

        colormap = ListedColormap(color_palette)

        ax = df_ventas_agrupado.plot(kind='bar', x='Producto', y='Subtotal', figsize=(10, 6), colormap=colormap)

        ax.grid(axis='y')

        for p in ax.patches:
            if p.get_height() > 0:
                ax.annotate(str(int(p.get_height())), (p.get_x() + p.get_width() / 2., p.get_height()), ha='center', va='bottom')
            else:
                ax.annotate(str(int(p.get_height())), (p.get_x() + p.get_width() / 2., p.get_height()), ha='center', va='top')

        ax.set_xlabel('Producto')  
        ax.set_ylabel('$ Total Ventas')  
        ax.set_title('Top 10 de Productos más Vendidos')  
        ax.set_xticklabels(df_ventas_agrupado['Producto'], rotation=45, ha='right')  
        plt.tight_layout()
        plt.savefig('./static/img/top_10_productos_mas_vendidos.png')
        plt.close()

    return total_ventas, ventas_detalle, df_ventas_agrupado

@ventas_page.route('/ganancias', methods=['GET', 'POST'])
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

        if len(ganancias_result) == 3:
            total_ventas, total_compras, img_url = ganancias_result
            ganancias = None  
        else:
            total_ventas, total_compras, ganancias, img_url = ganancias_result

        return render_template('ganancias.html', form=form, total_ventas=total_ventas, total_compras=total_compras, ganancias=ganancias, img_url=img_url)

    ganancias_result = calcular_ganancias()  
    if ganancias_result is None:
        flash("No hay datos de ganancias para la fecha seleccionada.", "warning")
        return render_template('ganancias.html', form=form)

    if len(ganancias_result) == 3:
        total_ventas, total_compras, img_url = ganancias_result
        ganancias = None  
    else:
        total_ventas, total_compras, ganancias, img_url = ganancias_result

    return render_template('ganancias.html', form=form, total_ventas=total_ventas, total_compras=total_compras, ganancias=ganancias, img_url=img_url)

def calcular_ganancias(tipo_seleccion=None, fecha_seleccionada=None):
    fecha_inicio, fecha_fin = calcular_rango_fechas(tipo_seleccion, fecha_seleccionada)

    total_ventas = calcular_total_ventas(fecha_inicio, fecha_fin)
    total_compras = calcular_total_compras(fecha_inicio, fecha_fin)
    if total_ventas == 0 and total_compras == 0:
        flash("No hay datos disponibles para la fecha seleccionada.", "warning")
        return None, None, None, None
    ganancias = total_ventas - total_compras

    if total_ventas is None or total_compras is None:
        flash("No hay datos disponibles para la fecha seleccionada.", "warning")
        return None, None, None, None

    plt.figure(figsize=(10, 6))  
    plt.pie([total_ventas, total_compras], labels=['Ventas\nCantidad: {}'.format(total_ventas), 'Gastos\nCantidad: {}'.format(total_compras)], startangle=140, counterclock=False, colors=['green', 'red'], wedgeprops=dict(width=0.4))
    plt.title('TentaCrisp S.A de CV\nEstado de resultados')

    centre_circle = plt.Circle((0, 0), 0.70, fc='white')
    fig = plt.gcf()
    fig.gca().add_artist(centre_circle)

    img_path = './static/img/total_ventas_compras_dona.png'
    plt.savefig(img_path)
    plt.close()

    img_url = url_for('static', filename='img/total_ventas_compras_dona.png')

    return total_ventas, total_compras, ganancias, img_url

def calcular_rango_fechas(tipo_seleccion=None, fecha_seleccionada=None):
    if tipo_seleccion == 'dia':
        fecha_inicio = fecha_seleccionada
        fecha_fin = fecha_seleccionada + timedelta(days=1)
    elif tipo_seleccion == 'semana':
        fecha_inicio_semana = fecha_seleccionada - timedelta(days=fecha_seleccionada.weekday())
        fecha_fin_semana = fecha_inicio_semana + timedelta(days=7)
        fecha_inicio = fecha_inicio_semana
        fecha_fin = fecha_fin_semana
    elif tipo_seleccion == 'mes':
        primer_dia_mes = fecha_seleccionada.replace(day=1)
        ultimo_dia_mes = primer_dia_mes.replace(day=1, month=primer_dia_mes.month % 12 + 1) - timedelta(days=1)
        fecha_inicio = primer_dia_mes
        fecha_fin = ultimo_dia_mes
    else:
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
    query_compras = db.session.query(func.sum(MateriaPrima.precioCompra))
    
    if fecha_inicio is not None and fecha_fin is not None:
        query_compras = query_compras.select_from(Detalle_materia_prima).join(MateriaPrima).filter(Detalle_materia_prima.fechaCompra.between(fecha_inicio, fecha_fin))
    else:
        query_compras = query_compras.select_from(MateriaPrima)
    
    total_compras_materia_prima = query_compras.scalar()

    if total_compras_materia_prima is None:
        total_compras_materia_prima = 0.0

    print("Total de compras de materia prima:", total_compras_materia_prima)

    query_merma_producto = db.session.query(func.sum(Merma.cantidadMerma * Producto.precioVenta))
    
    if fecha_inicio is not None and fecha_fin is not None:
        query_merma_producto = query_merma_producto.join(Producto, Merma.idProducto == Producto.idProducto).filter(Merma.fechaMerma.between(fecha_inicio, fecha_fin))
    
    total_merma_producto = query_merma_producto.scalar()

    if total_merma_producto is None:
        total_merma_producto = 0.0

    print("Total de merma de producto:", total_merma_producto)

    total_merma_inventario = calcular_valor_total_mermaInventario(fecha_inicio, fecha_fin)
    
    print("Total de merma de inventario:", total_merma_inventario)
    
    total_precio_produccion= calcular_precio_produccion_galletas_vendidas(fecha_inicio, fecha_fin)
    
    print("Total de precio de produccion:", total_precio_produccion)

    total_compras = total_compras_materia_prima + total_merma_producto + total_merma_inventario + total_precio_produccion

    print("Total de compras con merma:", total_compras)

    return total_compras

def calcular_valor_total_mermaInventario(fecha_inicio=None, fecha_fin=None):
    merma = merma_inventario.query.filter(merma_inventario.fechaMerma.between(fecha_inicio, fecha_fin)).all()

    cantidad_total_merma = sum(m.cantidadMerma for m in merma)

    compras = Compra.query.join(Detalle_materia_prima).all()
    precio_total_compras = sum(MateriaPrima.query.filter_by(idMateriaPrima=compra.idMateriaPrima).first().precioCompra for compra in compras)

    if precio_total_compras != 0:
        precio_por_unidad = precio_total_compras / sum(compra.cantidadExistentes for compra in compras)
    else:
        precio_por_unidad = 0.0

    valor_total_merma = cantidad_total_merma * precio_por_unidad

    return valor_total_merma

def calcular_precio_produccion_galletas_vendidas(fecha_inicio=None, fecha_fin=None):

    ventas = Venta.query.filter(Venta.fechaVenta.between(fecha_inicio, fecha_fin)).all()

    precio_produccion_galletas_vendidas = 0.0

    for venta in ventas:
        detalles_venta = DetalleVenta.query.filter_by(idVenta=venta.idVenta).all()
        for detalle in detalles_venta:
            producto = Producto.query.get(detalle.idProducto)
            precio_produccion_galletas_vendidas += detalle.cantidad * producto.precioProduccion

    return precio_produccion_galletas_vendidas


