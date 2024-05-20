$(document).ready(function() {
    let csvData = [];
    let fireYears = new Set();
    let states = new Set();
    let ecoregions = new Set();

    // Load CSV data
    $.ajax({
        url: 'https://wepp.cloud/geodata/mtbs/sbs/compiled_sbs.csv',
        dataType: 'text',
    }).done(function(data) {
        csvData = $.csv.toObjects(data);
        populateFilters(csvData);
        populateTable(csvData);
    });

    function populateFilters(data) {
        data.forEach(row => {
            const year = row.ignition_date.split('/')[2];
            fireYears.add(year);
            states.add(row.field_state);
            ecoregions.add(row.l3_ecoregion);
        });

        populateSelect('#fireYear', fireYears);
        populateSelect('#state', states);
        populateSelect('#ecoregion', ecoregions);
    }

    function populateSelect(selector, values) {
        values = Array.from(values).sort();
        values.forEach(value => {
            $(selector).append(new Option(value, value));
        });
    }

    $('#searchButton').click(function() {
        const fireName = $('#fireName').val().toLowerCase();
        const fireYear = $('#fireYear').val();
        const state = $('#state').val();
        const ecoregion = $('#ecoregion').val();

        const filteredData = csvData.filter(row => {
            const matchesFireName = row.fire_name.toLowerCase().includes(fireName);
            const matchesFireYear = fireYear === 'all' || row.ignition_date.split('/')[2] === fireYear;
            const matchesState = state === 'all' || row.field_state === state;
            const matchesEcoregion = ecoregion === 'all' || row.l3_ecoregion === ecoregion;
            return matchesFireName && matchesFireYear && matchesState && matchesEcoregion;
        });

        populateTable(filteredData);
    });



    function populateTable(data) {
        const tbody = $('#resultsTable tbody');
        tbody.empty();

        // fire_id,fire_name,ignition_date,administrative_unit,field_state,l3_ecoregion,standardized_sbs,field_acres,low_px,moderate_px,high_px
        data.forEach(row => {
            const fileName = row.standardized_sbs.split('/').pop();

            const tr = $('<tr>');
            tr.append($('<td>').text(row.fire_id));
            tr.append($('<td>').text(row.fire_name));
            tr.append($('<td>').text(row.ignition_date));
            tr.append($('<td>').text(row.administrative_unit));
            tr.append($('<td>').text(row.field_state));
            tr.append($('<td>').text(row.l3_ecoregion));
            tr.append($('<td>').html('<a href="https://wepp.cloud/geodata/mtbs/sbs/' + row.standardized_sbs + '" target="_blank">Download</a>'));
            tr.append($('<td>').html('<a href="https://dev.wepp.cloud/weppcloud/create/disturbed9002?landuse:sbs_map=https://wepp.cloud/geodata/mtbs/sbs/' 
                                     + row.standardized_sbs + '" target="_blank">Create WEPPcloud Project</a>'));
            tr.append($('<td>').text(row.field_acres));
            tr.append($('<td>').text(row.low_px));
            tr.append($('<td>').text(row.moderate_px));
            tr.append($('<td>').text(row.high_px));
            tbody.append(tr);
        });
    }
});

