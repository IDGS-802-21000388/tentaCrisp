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

