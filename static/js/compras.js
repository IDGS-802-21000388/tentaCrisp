$(document).ready(function() {
    var table = $('#tblCompras').DataTable({
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

    // Función para calcular el total y actualizarlo en la tabla
    function calcularTotal() {
        var total = 0;
        table.rows({search: 'applied'}).every(function() {
            var rowData = this.data();
            var totalFila = parseFloat(rowData[5]);
            total += totalFila;
        });

        // Actualizar el texto del elemento con id "total"
        $('#total').text(total.toFixed(2));
    }

    // Calcular el total inicialmente
    calcularTotal();

    // Escuchar el evento de dibujar (draw) y calcular el total
    table.on('draw', function() {
        calcularTotal();
    });

    // Escuchar el evento de búsqueda (search) y calcular el total
    table.on('search.dt', function() {
        calcularTotal();
    });
});
function toggleGrafica() {
    var graficaContainer = document.getElementById("grafica-container");
    if (graficaContainer.style.display === "none") {
      graficaContainer.style.display = "block";
    } else {
      graficaContainer.style.display = "none";
    }
  }