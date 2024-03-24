window.addEventListener('load', function() {
    var bodyTablaInventario = document.getElementById('bodyTablaInventario');
    var datosMateriaPrima = JSON.parse(bodyTablaInventario.getAttribute('data-materia-prima'));
    cargarTabla(datosMateriaPrima);
});

function reproducirVideo() {
    var video = document.getElementById("videoPlayer");
    video.autoplay = true;

    video.loop = true;

    video.style.display = "block";
}

window.onblur = function() {
    reproducirVideo();
};

function cargarTabla(data) {
    console.log(data);

    // Destruye la tabla si ya existe
    if ($.fn.DataTable.isDataTable('#tblMateria')) {
        $('#tblMateria').DataTable().destroy();
        $('#tblMateria tbody').empty();
    }

    // Generar tabla dinámica
    for (let i = 0; i < data.length; i++) {
        const fechaCompraSubstring = cambiarFormatoFechaTabla(data[i]['fechaCompra'].substring(0, 10));
        const fechaVencimientoSubstring = cambiarFormatoFechaTabla(data[i]['fechaVencimiento'].substring(0, 10));

        var precioCompraConSigno = data[i]['precioCompra'] + ' MXN ';
        var porcentajeConSigno = data[i]['porcentaje'] + ' % ';

        let fila = `<tr>
                        <td>${data[i]['nombreMateria']}</td>
                        <td>${data[i]['cantidadExistentes']}</td>
                        <td>${data[i]['medida']['tipoMedida']}</td>
                        <td>${precioCompraConSigno}</td>
                        <td>${fechaCompraSubstring}</td>
                        <td>${fechaVencimientoSubstring}</td>
                        <td>${porcentajeConSigno}</td>
                        <td><button data-idmateriaprima="${data[i]['idMateriaPrima']}" id="btnEliminar" class="btnEliminar"><i class="fa-solid fa-trash" style="color: #c12525;"></i></button></td>
                        <td><button data-idmateriaprima="${data[i]['idMateriaPrima']}" id="btnEditar" class="btnEditar"><i class="fa-solid fa-pen-to-square" style="color: #57351f;"></i></button></td>
                    </tr>`;

        $('#tblMateria tbody').append(fila);
    }

    // Inicializa DataTable después de agregar las filas
    $('#tblMateria').DataTable({
        dom: "<'row' <'col-sm-6'l><'col-sm-5'f>>  <'row' <'col-sm-12'tr>>  <'row' <'col-4'i><'col'p>>",
        initComplete: function () {
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
                previous: "Anterior",
            }
        },
        "ordering": false,
        retrieve: true
    });

    $('#agregarMaterialPrima').on('click', 'button', function () {
        $('#modalMaterialPrima').modal('show');
    });
}
