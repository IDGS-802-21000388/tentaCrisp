from flask import request, render_template, flash, redirect, url_for, Blueprint
import forms
from flask_login import login_required, current_user
from functools import wraps
from models import db, Proveedor

proveedor_page = Blueprint('proveedor', __name__,
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

def admin_required(f):
    @wraps(f)
    def decorated_function(*args, **kwargs):
        if current_user.rol != 'Administrador':
            flash('No tienes permisos', 'warning')
            return redirect(url_for('index'))
        return f(*args, **kwargs)
    return decorated_function

@proveedor_page.route("/proveedor", methods=['GET', 'POST'])
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
                flash('Proveedor agregado correctamente.','success')
            except Exception as e:
                flash('Error al agregar el proveedor a la base de datos.','error')

    proveedores = Proveedor.query.all()

    return render_template("provedor.html", form=provedor, proveedores=proveedores)

# Ruta para eliminar un Proveedor
@proveedor_page.route("/eliminar_proveedor", methods=['POST'])
@login_required
def eliminar_proveedor():
    id_proveedor = int(request.form.get("id"))
    proveedor = Proveedor.query.get(id_proveedor)
    if proveedor:
        proveedor.estatus = 0  # Cambiar el estado del usuario a inactivo
        db.session.commit()
        flash('Proveedor eliminado correctamente.', 'success')
    else:
        flash('Proveedor no encontrado.', 'error')
    return redirect(url_for('proveedor'))

# Ruta para editar un Proveedor
@proveedor_page.route('/editar_proveedor', methods=['POST'])
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
            flash('Proveedor editado correctamente.', 'success')
        except Exception as e:
            flash('Error al editar el proveedor a la base de datos.', 'error')
    else:
        flash('Proveedor no encontrado', 'error')

    return redirect(url_for('proveedor.proveedor'))