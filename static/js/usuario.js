$(document).ready(function() {
    $('#tblUsuario').DataTable({
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
    $('.btnEditar').click(function() {
        var idUsuario = $(this).data('idusuario');
        var nombre = $(this).data('nombre');
        var nombreUsuario = $(this).data('nombreusuario'); // Revisa la capitalización del nombre del atributo
        var contrasenia = $(this).data('contrasenia');
        var rol = $(this).data('rol');
        var telefono = $(this).data('telefono');
        
        // Llenar el formulario de edición con los detalles del usuario
        $('#editIdUsuario').val(idUsuario);
        $('#editNombre').val(nombre);
        $('#editNombreUsuario').val(nombreUsuario);
        $('#editContrasenia').val(contrasenia);
        $('#editRol').val(rol);
        $('#editTelefono').val(telefono);
        
        $('#modalUsuarioEditar').modal('show'); // Mostrar el modal
    });
});

$(document).ready(function() {
    $('.btnEliminar').click(function(event) {
        event.preventDefault(); // Prevenir el envío del formulario por defecto

        var form = $(this).closest('form');

        Swal.fire({
            title: '¿Estás seguro?',
            text: "¡No podrás revertir esto!",
            icon: 'warning',
            showCancelButton: true,
            confirmButtonColor: '#3085d6',
            cancelButtonColor: '#d33',
            confirmButtonText: 'Sí, eliminarlo!'
        }).then((result) => {
            if (result.isConfirmed) {
                form.off('submit'); // Desvincular el evento submit para evitar la recursividad

                // Envía el formulario manualmente después de cerrar la alerta
                form.submit();
            }
        });
    });
});


