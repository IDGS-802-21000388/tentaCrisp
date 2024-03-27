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

$(document).ready(function(){
    $(".editar").click(function(){
        var idProveedor = $(this).data("id");
        // Realiza una solicitud al servidor para obtener los datos del proveedor con el ID correspondiente
        $.get("/obtener_datos_proveedor?id=" + idProveedor, function(data, status){
            // Llena los campos del formulario en el modal con los datos obtenidos
            $("#txtIdProvedor").val(data.idProveedor);
            $("#nombreProveedor").val(data.nombreProveedor);
            $("#direccion").val(data.direccion);
            $("#telefono").val(data.telefono);
            $("#nombreAtiende").val(data.nombreAtiende);

            // Abre el modal
            $('#modalProveedorEditar').modal('show');
        });
    });
});
