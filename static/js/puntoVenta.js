let precioGalleta = 0;
let subtotales = {};

function agregarAlCarrito(event, idProducto, nombreProducto, precioProducto) {
    precioGalleta = precioProducto;
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
                <td><input type="number" name="cantidad"  onchange="actualizarPiezas('${idProducto}', this.value)" value="${cantidad}" min="1"></td>
                <td><input type="number" name="caja700g" value="0" min="0" onchange="actualizarCaja700g('${idProducto}', this.value)"></td>
                <td><input type="number" name="caja1k" value="0" min="0" onchange="actualizarCaja1kg('${idProducto}', this.value)"></td>
                <td><input type="number" name="gramos" value="0" min="0" onchange="actualizarGramos('${idProducto}', this.value)"></td>
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


function actualizarSubtotal(idProducto, nuevaCantidad, precioProducto) {
    const subtotal = nuevaCantidad * precioProducto;
    document.getElementById(`subtotal-${idProducto}`).textContent = `$${subtotal.toFixed(2)}`;
    
    subtotales[idProducto] = subtotal;
    recalcularTotal();
}

function actualizarPiezas(idProducto, nuevaCantidad) {
    const cantidadPiezas = parseInt(document.getElementById(`fila-${idProducto}`).querySelector('input[name="cantidad"]').value);
    const cantidadCajas700g = parseInt(document.getElementById(`fila-${idProducto}`).querySelector('input[name="caja700g"]').value);
    const cantidadCajas1kg = parseInt(document.getElementById(`fila-${idProducto}`).querySelector('input[name="caja1k"]').value);
    const cantidadGramos = parseInt(document.getElementById(`fila-${idProducto}`).querySelector('input[name="gramos"]').value);
    console.log(cantidadPiezas , cantidadCajas700g , cantidadCajas1kg , cantidadGramos);

    
    let subtotal700g = cantidadCajas700g * (precioGalleta * 35);
    let subtotal1kg = cantidadCajas1kg *(precioGalleta * 50);
    let subtotalGramos = parseInt(cantidadGramos / 20) * precioGalleta;
    let subtotalProducto = ((cantidadPiezas * 5) + subtotal700g + subtotal1kg + subtotalGramos) ;
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
    const cantidadPiezas = parseInt(document.getElementById(`fila-${idProducto}`).querySelector('input[name="cantidad"]').value);
    const cantidadCajas700g = parseInt(document.getElementById(`fila-${idProducto}`).querySelector('input[name="caja700g"]').value);
    const cantidadCajas1kg = parseInt(document.getElementById(`fila-${idProducto}`).querySelector('input[name="caja1k"]').value);
    const cantidadGramos = parseInt(document.getElementById(`fila-${idProducto}`).querySelector('input[name="gramos"]').value);
    console.log(cantidadPiezas , cantidadCajas700g , cantidadCajas1kg , cantidadGramos);

    let subtotal700g = cantidadCajas700g * (precioGalleta * 35);
    let subtotal1kg = cantidadCajas1kg *(precioGalleta * 50);
    let subtotalGramos = parseInt(cantidadGramos / 20) * precioGalleta;
    let subtotalProducto = ((cantidadPiezas * 5) + subtotal700g + subtotal1kg + subtotalGramos) ;
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
    const cantidadPiezas = parseInt(document.getElementById(`fila-${idProducto}`).querySelector('input[name="cantidad"]').value);
    const cantidadCajas700g = parseInt(document.getElementById(`fila-${idProducto}`).querySelector('input[name="caja700g"]').value);
    const cantidadCajas1kg = parseInt(document.getElementById(`fila-${idProducto}`).querySelector('input[name="caja1k"]').value);
    const cantidadGramos = parseInt(document.getElementById(`fila-${idProducto}`).querySelector('input[name="gramos"]').value);
    console.log(cantidadPiezas , cantidadCajas700g , cantidadCajas1kg , cantidadGramos);
    
    let subtotal700g = cantidadCajas700g * (precioGalleta * 35);
    let subtotal1kg = cantidadCajas1kg *(precioGalleta * 50);
    let subtotalGramos = parseInt(cantidadGramos / 20) * precioGalleta;
    let subtotalProducto = ((cantidadPiezas * 5) + subtotal700g + subtotal1kg + subtotalGramos) ;
    //const subtotalProducto = (cantidadPiezas + cantidadCajas700g * 35 + cantidadCajas1kg * 50 + cantidadGramos / 20) * precioGalleta;
    
    document.getElementById(`subtotal-${idProducto}`).textContent = `$${subtotalProducto.toFixed(2)}`;
    
    subtotales[idProducto] = subtotalProducto;
    recalcularTotal();
    let datos = JSON.stringify(obtenerDatosTabla());
    document.getElementById('datos').value = datos;
    document.getElementById('datos2').value = datos;
}

function actualizarGramos(idProducto, nuevaCantidad) {
    const cantidadPiezas = parseInt(document.getElementById(`fila-${idProducto}`).querySelector('input[name="cantidad"]').value);
    const cantidadCajas700g = parseInt(document.getElementById(`fila-${idProducto}`).querySelector('input[name="caja700g"]').value);
    const cantidadCajas1kg = parseInt(document.getElementById(`fila-${idProducto}`).querySelector('input[name="caja1k"]').value);
    const cantidadGramos = parseInt(document.getElementById(`fila-${idProducto}`).querySelector('input[name="gramos"]').value);
    console.log(cantidadPiezas , cantidadCajas700g , cantidadCajas1kg , cantidadGramos);
    
    let subtotal700g = cantidadCajas700g * (precioGalleta * 35);
    let subtotal1kg = cantidadCajas1kg *(precioGalleta * 50);
    let subtotalGramos = parseInt(cantidadGramos / 20) * precioGalleta;
    let subtotalProducto = ((cantidadPiezas * 5) + subtotal700g + subtotal1kg + subtotalGramos) ;
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
