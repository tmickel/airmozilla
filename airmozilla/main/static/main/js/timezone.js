$(function() {
    'use strict';
    $('time.jstime').each(function(i, time) {
        // Find all relevant <time> elements and replace with local time.
        var datetime = $(time).attr('datetime');
        var parsed = Date.parse(datetime);
        $(time).text(new Date(parsed));
    });
});
