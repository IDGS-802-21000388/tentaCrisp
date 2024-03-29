$(document).ready(function() {
    $('form').submit(function(event) {
        event.preventDefault();
        var formData = $(this).serialize();
        $.ajax({
            type: 'POST',
            url: '/',
            data: formData,
            dataType: 'json',
            success: function(response) {
                if (response.success) {
                    mostrarAlerta("success", "Inicio de sesión exitoso");

                    setTimeout(function() {
                        if (response.redirect) {
                            window.location.href = response.redirect;
                        }
                    }, 3000);
                } else {
                    mostrarAlerta("error", "Error: " + response.error);
                }
            },
            error: function(xhr, status, error) {
                mostrarAlerta("error", "Tu cuenta ha sido bloqueda por 1 minuto.");
            }
        });
    });
});

function mostrarAlerta(icono, mensaje) {
    const Toast = Swal.mixin({
        toast: true,
        position: "bottom",
        showConfirmButton: false,
        timer: 2000,
        timerProgressBar: true,
        didOpen: (toast) => {
            toast.onmouseenter = Swal.stopTimer;
            toast.onmouseleave = Swal.resumeTimer;
        }
    });
    Toast.fire({
        icon: icono,
        title: mensaje
    });
}
