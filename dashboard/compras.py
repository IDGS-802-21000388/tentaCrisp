import os
from flask import request, render_template, flash, redirect, url_for, Blueprint, current_app
from flask_login import current_user, login_required
from functools import wraps
from models import MateriaPrima, Detalle_materia_prima, Compra, merma_inventario
import pandas as pd
import forms
from datetime import datetime, timedelta

compras_page = Blueprint('compras', __name__, 
                          static_folder='static', 
                          template_folder='templates'
                          )

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




@compras_page.route('/compras', methods=['POST', 'GET'])
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
        return None, None  

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
    img_path = os.path.join(compras_page.root_path,'..', 'static', 'img', 'compras.png')
    fig.savefig(img_path)
    img_url = url_for('static', filename='img/compras.png')
    
    return compras, img_url


def calcular_rango_fechas(tipo_busqueda=None, fecha_seleccionada=None):
    if tipo_busqueda == 'dia':
        fecha_inicio = fecha_seleccionada
        fecha_fin = fecha_seleccionada + timedelta(days=1)
    elif tipo_busqueda == 'semana':
        fecha_inicio_semana = fecha_seleccionada - timedelta(days=fecha_seleccionada.weekday())
        fecha_fin_semana = fecha_inicio_semana + timedelta(days=7)
        fecha_inicio = fecha_inicio_semana
        fecha_fin = fecha_fin_semana
    elif tipo_busqueda == 'mes':
        primer_dia_mes = fecha_seleccionada.replace(day=1)
        ultimo_dia_mes = primer_dia_mes.replace(day=1, month=primer_dia_mes.month % 12 + 1) - timedelta(days=1)
        fecha_inicio = primer_dia_mes
        fecha_fin = ultimo_dia_mes
    else:
        fecha_inicio = datetime.min
        fecha_fin = datetime.max
    
    return fecha_inicio, fecha_fin

def calcular_total_compras():
    compras = Detalle_materia_prima.query.all()

    total_compras = 0.0

    for compra in compras:
        materia_prima = MateriaPrima.query.get(compra.idMateriaPrima)
        if materia_prima:
            total_compras += materia_prima.precioCompra * compra.cantidadExistentes

    return total_compras
