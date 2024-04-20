$(document).ready(function() {
    $('#tblMateriaPrima').DataTable({
        dom: "<'row' <'col-sm-6'l><'col-sm-5'f>>  <'row' <'col-sm-12'tr>>  <'row' <'col-4'i><'col'p>>",
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

$(document).ready(function() {
    $('#tblMateriaPrimaDatos').DataTable({
        dom: "<'row' <'col-sm-6'l><'col-sm-5'f>>  <'row' <'col-sm-12'tr>>  <'row' <'col-4'i><'col'p>>",
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

document.getElementById('tipo_compra').addEventListener('change', function() {
    var tipoCompra = this.value;
    if (tipoCompra === 'bulto') {
        document.getElementById('campo_extra_bulto').style.display = 'block';
        document.getElementById('campo_extra_caja').style.display = 'none';
    } else if (tipoCompra === 'caja') {
        document.getElementById('campo_extra_bulto').style.display = 'none';
        document.getElementById('campo_extra_caja').style.display = 'block';
    } else if (tipoCompra === 'unidad') {
        document.getElementById('campo_extra_bulto').style.display = 'none';
        document.getElementById('campo_extra_caja').style.display = 'none';
    }
});

document.getElementById('tipo_compraEdit').addEventListener('change', function() {
    var tipoCompra = this.value;
    if (tipoCompra === 'bulto') {
        document.getElementById('campo_extra_bulto_Edit').style.display = 'block';
        document.getElementById('campo_extra_caja_Edit').style.display = 'none';
    } else if (tipoCompra === 'caja') {
        document.getElementById('campo_extra_bulto_Edit').style.display = 'none';
        document.getElementById('campo_extra_caja_Edit').style.display = 'block';
    }else if (tipoCompra === 'unidad') {
        document.getElementById('campo_extra_bulto_Edit').style.display = 'none';
        document.getElementById('campo_extra_caja_Edit').style.display = 'none';
    }
});

document.getElementById('btnVerUltimosIngredientes').addEventListener('click', function() {
    var ultimosIngredientes = document.getElementById('ultimosIngredientes');
    if (ultimosIngredientes.style.display === 'none') {
        ultimosIngredientes.style.display = 'block';
    } else {
        ultimosIngredientes.style.display = 'none';
    }
});

$(document).ready(function() {
    $('.btnMerma').click(function() {
        var idMateria = $(this).data('id');
        var idDetalle = $(this).data('idD');
        console.log("Detalle idDetalle " + idDetalle);
        console.log("Detalle idMateria " + idMateria);

        $('#idDetalle').val(idDetalle);
        $('#idMateria').val(idMateria);
        
        $('#modalMerma').modal('show');
    });
});

$(document).ready(function() {
    $('.btnEditarMateria').click(function() {
        var idDetalle = $(this).data('id');
        var nombreProducto = $(this).data('nombreproducto');
        var precioCompra = $(this).data('preciocompra');
        var cantidad = $(this).data('cantidad');
        var tipo = $(this).data('tipo');
        var fechaCompra = $(this).data('fechacompra');
        var fechaVencimiento = $(this).data('fechavencimiento');
        var porcentaje = $(this).data('porcentaje');
        var proveedor = $(this).data('proveedor');


        $('#editIdMateria').val(idDetalle);
        $('#editNombreProducto').val(nombreProducto);
        $('#editPrecioCompra').val(precioCompra);
        $('#editCantidad').val(cantidad);
        $('#editFechaVencimiento').val(fechaVencimiento);
        
        $('#modalMateriaEditar').modal('show');
    });
});


function clean(){
    document.getElementById("txtNombre").value = "";
    document.getElementById("txtPrecioCompra").value = "";
    document.getElementById("txtCantidad").value = "";
    document.getElementById("txtFechaVencimiento").value = "";
}
function bloquearTexto(event) {
    var keyCode = event.keyCode || event.which;

    if (keyCode == 8 || keyCode == 46) {
        return;
    }

    var key = String.fromCharCode(!event.charCode ? event.which : event.charCode);

    // Expresión regular que permite solo números
    var regex = /^[0-9]+$/;

    if (!regex.test(key)) {
        event.preventDefault();
    }
}

document.getElementById('kilos_bulto').addEventListener('keydown', bloquearTexto);
document.getElementById('numero_piezas_caja').addEventListener('keydown', bloquearTexto);

document.getElementById('kilos_bulto').addEventListener('keydown', bloquearTexto);
document.getElementById('numero_piezas_caja').addEventListener('keydown', bloquearTexto);



