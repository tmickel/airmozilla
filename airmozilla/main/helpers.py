import jinja2

from jingo import register


@register.filter
def js_date(datetime, format='ddd, MMM D, YYYY, h:mma UTCZZ'):
    """ Python datetime to a time tag with JS Date.parse-parseable format. """
    date = '%i/%i/%i' % (datetime.month, datetime.day, datetime.year)
    time = str(datetime.time())
    tz = datetime.tzname()  # Should always be UTC
    formatted_datetime = ' '.join([date, time, tz])
    return jinja2.Markup('<time datetime="%s" class="jstime" \
                           data-format="%s">%s</time>'
                 % (formatted_datetime, format, formatted_datetime))
