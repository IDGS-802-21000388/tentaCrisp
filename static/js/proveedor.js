$('#tblProveedor').DataTable({
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

function eliminarProveedor(idProveedor) {
    if (confirm('¿Estás seguro de que quieres eliminar este proveedor?')) {
        window.location.href = '/eliminar_proveedor?id=' + idProveedor;
    }
}

$(document).ready(function(){
    $(".eliminar").click(function(){
        var idProveedor = $(this).data("id");
        eliminarProveedor(idProveedor);
    });
});

$(document).ready(function() {
    $('.btnEditarProveedor').click(function() {
        console.log("HOLAAA 2 " + $(this).data('id') + " " + $(this).data('nombreproveedor') + " " + $(this).data('direccion') + " " + $(this).data('telefono') + " " + $(this).data('nombreatiende') + " ");
        var idProveedor = $(this).data('id');
        console.log("HOLAAA "+ idProveedor);
        var nombreProveedor = $(this).data('nombreproveedor');
        var direccion = $(this).data('direccion');
        var telefono = $(this).data('telefono');
        var nombreAtiende = $(this).data('nombreatiende');
        
        // Llenar el formulario de edición con los detalles del proveedor
        $('#editIdProveedor').val(idProveedor);
        $('#editNombreProveedor').val(nombreProveedor);
        $('#editDireccion').val(direccion);
        $('#editTelefono').val(telefono);
        $('#editNombreAtiende').val(nombreAtiende);
        
        $('#modalProveedorEditar').modal('show'); // Mostrar el modal
    });
});

