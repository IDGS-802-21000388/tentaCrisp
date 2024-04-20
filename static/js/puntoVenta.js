let precioGalleta = 0;
let subtotales = {};
let preciosData = [];

function agregarAlCarrito(event, idProducto, nombreProducto, precioProducto) {
    precioGalleta = precioProducto;

    let precioData = {
        idProducto: idProducto,
        nombreProducto: nombreProducto,
        precioProducto: precioProducto
    };
    preciosData.push(precioData);
    document.getElementById('btnGenerarVenta').disabled = false;
    document.getElementById('btnGenerarVentaTicket').disabled = false;

    event.preventDefault();
    
    const cantidadInput = event.target.querySelector('input[name="cantidad"]');
    const cantidad = parseInt(cantidadInput.value);
    const filaExistente = document.getElementById(`fila-${idProducto}`);
    
    cantidadInput.addEventListener('change', function() {
        const nuevaCantidad = parseInt(this.value);
        actualizarCantidadGenerada(idProducto, nuevaCantidad);
    });
    
    if (filaExistente) {
        const cantidadExistente = parseInt(filaExistente.querySelector('input[type="number"]').value);
        const nuevaCantidad = cantidadExistente + cantidad;
        filaExistente.querySelector('input[type="number"]').value = nuevaCantidad;
        actualizarSubtotal(idProducto, nuevaCantidad, precioProducto);
    } else {
        const fila = `
            <tr id="fila-${idProducto}">
                <td>${nombreProducto}</td>
                <td><input type="number" name="cantidad" class="form-control" style=" width: 100px;" onchange="actualizarPiezas('${idProducto}', this.value)" value="${cantidad}" min="1"></td>
                <td><input type="number" name="caja700g" class="form-control" style=" width: 100px;" value="0" min="0" onchange="actualizarCaja700g('${idProducto}', this.value)"></td>
                <td><input type="number" name="caja1k" class="form-control" style=" width: 100px;" value="0" min="0" onchange="actualizarCaja1kg('${idProducto}', this.value)"></td>
                <td><input type="number" name="gramos" class="form-control" style=" width: 100px;" value="0" min="0" onchange="actualizarGramos('${idProducto}', this.value)"></td>
                <td id="subtotal-${idProducto}">$${(cantidad * precioProducto).toFixed(2)}</td>
                <td><button onclick="eliminarGalleta('${idProducto}')">Eliminar</button></td>
            </tr>
        `;
        document.getElementById('carrito-body').insertAdjacentHTML('beforeend', fila);
    }
    

    function actualizarCantidadGenerada(idProducto, nuevaCantidad) {
        const subtotal = nuevaCantidad * precioGalleta;
        subtotales[idProducto] = subtotal;
    }

    const subtotal = cantidad * precioProducto;
    subtotales[idProducto] = subtotal;
}

function eliminarGalleta(idProducto) {
    const fila = document.getElementById(`fila-${idProducto}`);
    if (fila) {
        fila.remove();
        recalcularTotal();
    }

    const filasTabla = document.querySelectorAll('#carrito-body tr');
    if (filasTabla.length === 0) {
        const totalElemento = document.getElementById('total');
        totalElemento.textContent = '$0.00';
    }
}

function buscarPrecioPorId(id) {
    // Utiliza el método find para buscar el precio con el ID dado
    const precioEncontrado = preciosData.find(precio => precio.idProducto === id);
    
    // Si se encuentra el precio, devuélvelo; de lo contrario, devuelve null
    return precioEncontrado ? precioEncontrado.precioProducto : null;
}

function actualizarSubtotal(idProducto, nuevaCantidad, precioProducto) {
    const subtotal = nuevaCantidad * precioProducto;
    document.getElementById(`subtotal-${idProducto}`).textContent = `$${subtotal.toFixed(2)}`;
    
    subtotales[idProducto] = subtotal;
    recalcularTotal();
}

function actualizarPiezas(idProducto, nuevaCantidad) {
    console.log("idProducto: " + idProducto);

    const precioEncontrado = buscarPrecioPorId(idProducto);
    
    const cantidadPiezas = parseInt(document.getElementById(`fila-${idProducto}`).querySelector('input[name="cantidad"]').value);
    const cantidadCajas700g = parseInt(document.getElementById(`fila-${idProducto}`).querySelector('input[name="caja700g"]').value);
    const cantidadCajas1kg = parseInt(document.getElementById(`fila-${idProducto}`).querySelector('input[name="caja1k"]').value);
    const cantidadGramos = parseInt(document.getElementById(`fila-${idProducto}`).querySelector('input[name="gramos"]').value);
    console.log(cantidadPiezas , cantidadCajas700g , cantidadCajas1kg , cantidadGramos);


    let subtotal700g = cantidadCajas700g * (precioEncontrado * 35);
    let subtotal1kg = cantidadCajas1kg *(precioEncontrado * 50);
    let subtotalGramos = parseInt(cantidadGramos / 20) * precioEncontrado;
    let subtotalProducto = ((cantidadPiezas * precioEncontrado) + subtotal700g + subtotal1kg + subtotalGramos) ;
    console.log(subtotalProducto , cantidadPiezas , subtotal700g , subtotal1kg , subtotalGramos , precioGalleta);
    //const subtotalProducto = (cantidadPiezas + cantidadCajas700g * 35 + cantidadCajas1kg * 50 + cantidadGramos / 20) * precioGalleta;
    
    document.getElementById(`subtotal-${idProducto}`).textContent = `$${subtotalProducto.toFixed(2)}`;
    
    subtotales[idProducto] = subtotalProducto;
    recalcularTotal();
    let datos = JSON.stringify(obtenerDatosTabla());
    document.getElementById('datos').value = datos;
    document.getElementById('datos2').value = datos;
}

function actualizarCaja700g(idProducto, nuevaCantidad) {
    console.log("idProducto: " + idProducto);
    const precioEncontrado = buscarPrecioPorId(idProducto);
    const cantidadPiezas = parseInt(document.getElementById(`fila-${idProducto}`).querySelector('input[name="cantidad"]').value);
    const cantidadCajas700g = parseInt(document.getElementById(`fila-${idProducto}`).querySelector('input[name="caja700g"]').value);
    const cantidadCajas1kg = parseInt(document.getElementById(`fila-${idProducto}`).querySelector('input[name="caja1k"]').value);
    const cantidadGramos = parseInt(document.getElementById(`fila-${idProducto}`).querySelector('input[name="gramos"]').value);
    console.log(cantidadPiezas , cantidadCajas700g , cantidadCajas1kg , cantidadGramos);

    let subtotal700g = cantidadCajas700g * (precioEncontrado * 35);
    let subtotal1kg = cantidadCajas1kg *(precioEncontrado * 50);
    let subtotalGramos = parseInt(cantidadGramos / 20) * precioEncontrado;
    let subtotalProducto = ((cantidadPiezas * precioEncontrado) + subtotal700g + subtotal1kg + subtotalGramos) ;
    console.log(subtotalProducto , cantidadPiezas , subtotal700g , subtotal1kg , subtotalGramos , precioGalleta);
    //const subtotalProducto = (cantidadPiezas + cantidadCajas700g * 35 + cantidadCajas1kg * 50 + cantidadGramos / 20) * precioGalleta;
    
    document.getElementById(`subtotal-${idProducto}`).textContent = `$${subtotalProducto.toFixed(2)}`;
    
    subtotales[idProducto] = subtotalProducto;
    recalcularTotal();
    let datos = JSON.stringify(obtenerDatosTabla());
    document.getElementById('datos').value = datos;
    document.getElementById('datos2').value = datos;
}

function actualizarCaja1kg(idProducto, nuevaCantidad) {
    console.log("idProducto: " + idProducto);
    const precioEncontrado = buscarPrecioPorId(idProducto);
    const cantidadPiezas = parseInt(document.getElementById(`fila-${idProducto}`).querySelector('input[name="cantidad"]').value);
    const cantidadCajas700g = parseInt(document.getElementById(`fila-${idProducto}`).querySelector('input[name="caja700g"]').value);
    const cantidadCajas1kg = parseInt(document.getElementById(`fila-${idProducto}`).querySelector('input[name="caja1k"]').value);
    const cantidadGramos = parseInt(document.getElementById(`fila-${idProducto}`).querySelector('input[name="gramos"]').value);
    console.log(cantidadPiezas , cantidadCajas700g , cantidadCajas1kg , cantidadGramos);
    
    let subtotal700g = cantidadCajas700g * (precioEncontrado * 35);
    let subtotal1kg = cantidadCajas1kg *(precioEncontrado * 50);
    let subtotalGramos = parseInt(cantidadGramos / 20) * precioEncontrado;
    let subtotalProducto = ((cantidadPiezas * precioEncontrado) + subtotal700g + subtotal1kg + subtotalGramos) ;
    console.log(subtotalProducto , cantidadPiezas , subtotal700g , subtotal1kg , subtotalGramos , precioGalleta);
    //const subtotalProducto = (cantidadPiezas + cantidadCajas700g * 35 + cantidadCajas1kg * 50 + cantidadGramos / 20) * precioGalleta;
    
    document.getElementById(`subtotal-${idProducto}`).textContent = `$${subtotalProducto.toFixed(2)}`;
    
    subtotales[idProducto] = subtotalProducto;
    recalcularTotal();
    let datos = JSON.stringify(obtenerDatosTabla());
    document.getElementById('datos').value = datos;
    document.getElementById('datos2').value = datos;
}

function actualizarGramos(idProducto, nuevaCantidad) {
    console.log("idProducto: " + idProducto);
    const precioEncontrado = buscarPrecioPorId(idProducto);
    const cantidadPiezas = parseInt(document.getElementById(`fila-${idProducto}`).querySelector('input[name="cantidad"]').value);
    const cantidadCajas700g = parseInt(document.getElementById(`fila-${idProducto}`).querySelector('input[name="caja700g"]').value);
    const cantidadCajas1kg = parseInt(document.getElementById(`fila-${idProducto}`).querySelector('input[name="caja1k"]').value);
    const cantidadGramos = parseInt(document.getElementById(`fila-${idProducto}`).querySelector('input[name="gramos"]').value);
    console.log(cantidadPiezas , cantidadCajas700g , cantidadCajas1kg , cantidadGramos);
    
    let subtotal700g = cantidadCajas700g * (precioEncontrado * 35);
    let subtotal1kg = cantidadCajas1kg *(precioEncontrado * 50);
    let subtotalGramos = parseInt(cantidadGramos / 20) * precioEncontrado;
    let subtotalProducto = ((cantidadPiezas * precioEncontrado) + subtotal700g + subtotal1kg + subtotalGramos) ;
    console.log(subtotalProducto , cantidadPiezas , subtotal700g , subtotal1kg , subtotalGramos , precioGalleta);
    //const subtotalProducto = (cantidadPiezas + cantidadCajas700g * 35 + cantidadCajas1kg * 50 + cantidadGramos / 20) * precioGalleta;
    
    document.getElementById(`subtotal-${idProducto}`).textContent = `$${subtotalProducto.toFixed(2)}`;
    
    subtotales[idProducto] = subtotalProducto;
    recalcularTotal();
    let datos = JSON.stringify(obtenerDatosTabla());
    document.getElementById('datos').value = datos;
    document.getElementById('datos2').value = datos;
}

function recalcularTotal() {
    let total = 0;
    for (const idProducto in subtotales) {
        total += subtotales[idProducto];
    }
    document.getElementById('total').textContent = `$${total.toFixed(2)}`;
}

function obtenerDatosTabla() {
    const datosTabla = [];

    const filas = document.querySelectorAll('#carrito tbody tr');
    
    filas.forEach(fila => {
        const id = parseInt(fila.id.split('-')[1]); // Obtener el ID de la fila
        const piezas = parseInt(fila.querySelector('td:nth-child(2) input').value);
        const caja700g = parseInt(fila.querySelector('td:nth-child(3) input').value);
        const caja1kg = parseInt(fila.querySelector('td:nth-child(4) input').value);
        const gramos = parseInt(fila.querySelector('td:nth-child(5) input').value);
        const subtotal = parseFloat(fila.querySelector('td:nth-child(6)').textContent.replace('$', ''));

        const datosFila = {
            id: id,
            piezas: piezas,
            caja700g: caja700g * 35 ,
            caja1kg: caja1kg * 50,
            gramos: gramos / 20,
            subtotal: subtotal
        };
        datosTabla.push(datosFila);
    });

    let datos = JSON.stringify(datosTabla);
    console.log("Datos Tabla: " + datos);
    return datosTabla;
}

function limpiarTabla() {
    var tabla = document.getElementById("carrito-body");

    var numRows = tabla.rows.length;
    
    for (var i = numRows - 1; i >= 0; i--) {
        tabla.deleteRow(i);
    }
    document.getElementById("total").textContent = "$0.00";
    
}


document.getElementById("btnLimpiar").addEventListener("click", function() {
    limpiarTabla();
});

document.getElementById("btnGenerarVentaTicket").addEventListener("click", function() {
    limpiarTabla();
});

function abrirModalSolicitud() {
    document.getElementById('modalSolicitud').style.display = 'block';
}

function cerrarModal() {
    document.getElementById('modalSolicitud').style.display = 'none';
}


function bloquearNoNumerico(event) {
    var keyCode = event.keyCode || event.which;

    // Permitir teclas de navegación y otras teclas especiales
    if (keyCode == 8 || keyCode == 46 || keyCode == 37 || keyCode == 39 || keyCode == 9) {
        return;
    }

    // Bloquear caracteres no numéricos
    if (keyCode < 48 || keyCode > 57) {
        event.preventDefault();
    }
}

function bloquearNumerosNegativos(event) {
    var keyCode = event.keyCode || event.which;

    if (keyCode == 8 || keyCode == 46) {
        return;
    }

    var key = String.fromCharCode(!event.charCode ? event.which : event.charCode);

    // Expresión regular que permite solo números positivos o 0
    var regex = /^[0-9]+$/;

    if (!regex.test(key)) {
        event.preventDefault();
    }
}

// Aplicar la función a los elementos de entrada
document.getElementsByName('cantidad')[0].addEventListener('keydown', function(event) {
    bloquearNoNumerico(event);
    bloquearNumerosNegativos(event);
    bloquearNumerosNegativos2(event);
});
document.getElementsByName('caja700g')[0].addEventListener('keydown', function(event) {
    bloquearNoNumerico(event);
    bloquearNumerosNegativos(event);
    bloquearNumerosNegativos2(event);
});
document.getElementsByName('caja1k')[0].addEventListener('keydown', function(event) {
    bloquearNoNumerico(event);
    bloquearNumerosNegativos(event);
    bloquearNumerosNegativos2(event);
});
document.getElementsByName('gramos')[0].addEventListener('keydown', function(event) {
    bloquearNoNumerico(event);
    bloquearNumerosNegativos(event);
    bloquearNumerosNegativos2(event);
});

function bloquearNumerosNegativos2(event) {
    var keyCode = event.keyCode || event.which;

    if (keyCode == 8 || keyCode == 46) {
        return;
    }

    var key = String.fromCharCode(!event.charCode ? event.which : event.charCode);

    // Expresión regular que permite solo números positivos o 0
    var regex = /^[0-9]+$/;

    // Permitir también el guion ( - ) solo en la primera posición  
    if (key === '-' && this.selectionStart === 0 && !this.value.includes('-')) {
        return;
    }

    if (!regex.test(key)) {
        event.preventDefault();
    }
}



