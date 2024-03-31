$('#tblCompras').DataTable({
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