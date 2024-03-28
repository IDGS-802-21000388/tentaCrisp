$(document).ready(function() {
    $('#tblProduccion').DataTable({
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

function confirmarAccion(idProducto, fechaVencimiento, accion) {
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
            document.getElementById("fecha_vencimiento1").value = fechaVencimiento;
            document.querySelector(".eliminarForm input[name='id_producto_" + idProducto + "']").parentNode.submit();
        }
    });
}
