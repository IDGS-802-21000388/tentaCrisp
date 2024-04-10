$(document).ready(function() {
    $('#btnIngredientes').click(function() {
        var cantidadPorcion = $('#txtCantidadPorcion').val();
        var ingredienteSeleccionado = $('#txtIngredientes option:selected').text();
        var idIngredienteSeleccionado = $('#txtIngredientes option:selected').attr('id');
                
        var newRow = `<tr>
                        <input type="hidden" name="ingredientes_${idIngredienteSeleccionado}" id="${idIngredienteSeleccionado}" value="${cantidadPorcion}">
                        <td value="${ingredienteSeleccionado}" id="${idIngredienteSeleccionado}"> ${ingredienteSeleccionado} </td>
                        <td> ${cantidadPorcion} gramos </td>
                        <td><button id="${idIngredienteSeleccionado}" class="btnEliminar"><i class="fa-solid fa-trash" style="color: #c12525;"></i></button></td>
                    </tr>`;
        $('#tbodyIngredientes').append(newRow);  
    });

    $('#btnIngredientesEditar').click(function() {
        var cantidadPorcion = $("#txtCantidadPorcionEditar").val(); 
        var ingredienteSeleccionado = $('#txtIngredientes_editar option:selected').text();
        var idIngredienteSeleccionado = $('#txtIngredientes_editar option:selected').attr('id');
        var newRow = `<tr>
                        <input type="hidden" name="ingredienteseditar_${idIngredienteSeleccionado}" id="${idIngredienteSeleccionado}" value="${cantidadPorcion}">
                        <td value="${ingredienteSeleccionado}" id="${idIngredienteSeleccionado}"> ${ingredienteSeleccionado} </td>
                        <td> ${cantidadPorcion} gramos</td>
                        <td><button id="${idIngredienteSeleccionado}" class="btnEliminar"><i class="fa-solid fa-trash" style="color: #c12525;"></i></button></td>
                    </tr>`;
        $('#tblIngredientesEditar tbody').append(newRow);  
    });
    
    $(document).on('click', '.btnEliminar', function(){
        event.preventDefault();
        var idFila = $(this).attr('id');
        $(this).closest('tr').remove();
    });

    $('#tblProductos').DataTable({
        dom: "<'row' <'col-sm-6'l><'col-sm-5'f>>  <'row' <'col-sm-12'tr>>  <'row' <'col-4'i><'col'p>>",
        columnDefs: [
            { targets: [1], visible: false }
        ],
        initComplete: function(){
            $('.dataTables_filter').addClass('text-end');
        },
        language: {
            decimal: "",
            emptyTable: "No hay información",
            info: "Mostrando _START_ a _END_ de _TOTAL_ Entradas",
            infoEmpty: "Mostrando 0 Entradas",
            infoFiltered: "",
            infoPostFix: "",
            thousands: ",",
            lengthMenu: "Mostrar   _MENU_  Entradas",
            loadingRecords: "Cargando...",
            processing: "Procesando...",
            search: " ",
            searchPlaceholder: "Buscar",
            zeroRecords: "Sin resultados encontrados",
            paginate: {
                first: "Primero",
                last: "Ultimo",
                next: "Siguiente",
                previous: "Anterior"
            }
        },
        "ordering": false,
        retrieve: true
    });
});

function confirmarAccion(idProducto, accion) {
    let confirmacionTexto = "";
    let confirmacionColor = "";

    if (accion === "eliminar") {
        confirmacionTexto = "¡El producto se eliminará de forma lógica!";
        confirmacionColor = "#3085d6";
    } else if (accion === "activar") {
        confirmacionTexto = "¡El producto se activará de forma lógica!";
        confirmacionColor = "#3085d6";
    }

    Swal.fire({
        title: "¿Estás seguro?",
        text: confirmacionTexto,
        icon: "warning",
        showCancelButton: true,
        confirmButtonColor: confirmacionColor,
        cancelButtonColor: "#d33",
        confirmButtonText: "Sí, continuar"
    }).then((result) => {
        if (result.isConfirmed) {
            document.querySelector(".eliminarForm input[name='id_producto_" + idProducto + "']").parentNode.submit();
        }
    });
}

$(document).on('click', '.btnEditar', function() {
    var nombreProducto = $(this).data('nombre');
    var cantidadExistentes = $(this).data('cantidad');
    var precioProduccion = $(this).data('precio-produccion');
    var precioVenta = $(this).data('precio-venta');
    var ingredientes = $(this).data('ingredientes');
    var foto = $(this).data('foto');
    var idProducto = $(this).data('prod')

    $('#product').val(idProducto);
    $('#txtEditarGalleta').val(nombreProducto);
    $('#txtCantidadExisEditar').val(cantidadExistentes);
    $('#txtPrecioProdEditar').val(precioProduccion);
    $('#txtPrecioVentaEditar').val(precioVenta);
    $('#imagenPreviewEditar').attr('src','data:image/jpeg;base64,'+foto);
    $('#tblIngredientesEditar tbody').empty();
    
    $.each(ingredientes, function(index, ingrediente) {
        var fila = '<tr>' +
            '<td>' + ingrediente.nombre + '</td>' +
            '<td>' + ingrediente.cantidad + ' gramos</td>' +
            '<input type="hidden" name="ingredienteseditar_'+ingrediente.id+'" value="' + ingrediente.cantidad + '">' +
            '<td><button id="'+ingrediente.id+'" class="btnEliminar"><i class="fa-solid fa-trash" style="color: #c12525;"></i></button></td>' +
            '</tr>';
        $('#tblIngredientesEditar tbody').append(fila); 
    });
});

$('#fotografiaInputEditar').change(function() {
    var input = this;
    if (input.files && input.files[0]) {
        var reader = new FileReader();
        reader.onload = function(e) {
            $('#imagenPreviewEditar').attr('src', e.target.result);
        }
        reader.readAsDataURL(input.files[0]);
    }
});

function mostrarImagen() {
    var input = document.getElementById('fotografiaInput');
    var preview = document.getElementById('imagenPreview');
    var file = input.files[0];
    var reader = new FileReader();
    reader.onload = function(e) {
        preview.src = e.target.result;
    }
    reader.readAsDataURL(file);
}
