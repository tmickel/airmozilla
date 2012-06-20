$(function() {
    'use strict';
    $('time.jstime').each(function(i, time) {
        // Find all relevant <time> elements and replace with formatted time.
        var datetime = $(time).attr('datetime');
        var format = $(time).attr('data-format');
        var parsed = moment(datetime);
        $(time).text(parsed.format(format));
    });
});
