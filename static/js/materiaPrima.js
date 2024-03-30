$('#tblMateriaPrima').DataTable({
    dom: "<'row' <'col-sm-6'l><'col-sm-5'f>>  <'row' <'col-sm-12'tr>>  <'row' <'col-4'i><'col'p>>",
    initComplete: function(){
        $('.dataTables_filter').addClass('text-end');
    },
    language: {
        decimal: "",
        emptyTable: "No hay información",
        info: "Mostrando START a END de TOTAL Entradas",
        infoEmpty: "Mostrando 0 Entradas",
        infoFiltered: "",
        infoPostFix: "",
        thousands: ",",
        lengthMenu: "Mostrar   MENU  Entradas",
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
    retrieve: true
    });

$('#tblMateriaPrimaDatos').DataTable({
    dom: "<'row' <'col-sm-6'l><'col-sm-5'f>>  <'row' <'col-sm-12'tr>>  <'row' <'col-4'i><'col'p>>",
    initComplete: function(){
        $('.dataTables_filter').addClass('text-end');
    },
    language: {
        decimal: "",
        emptyTable: "No hay información",
        info: "Mostrando START a END de TOTAL Entradas",
        infoEmpty: "Mostrando 0 Entradas",
        infoFiltered: "",
        infoPostFix: "",
        thousands: ",",
        lengthMenu: "Mostrar   MENU  Entradas",
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
    retrieve: true
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
        var idDetalle = $(this).data('id');
        console.log("Detalle" + idDetalle);

        $('#idDetalle').val(idDetalle);
        
        $('#modalMerma').modal('show');
    });
});

function clean(){
    document.getElementById("txtNombre").value = "";
    document.getElementById("txtPrecioCompra").value = "";
    document.getElementById("txtCantidad").value = "";
    document.getElementById("txtFechaVencimiento").value = "";
}



