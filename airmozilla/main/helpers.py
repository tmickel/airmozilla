import datetime
import jinja2

from jingo import register


@register.filter
def js_date(dt, format='ddd, MMM D, YYYY, h:mma UTCZZ'):
    """ Python datetime to a time tag with JS Date.parse-parseable format. """
    dt_date = dt.strftime('%m/%d/%Y')
    dt_time = dt.strftime('%H:%M')
    dt_tz = dt.tzname() or 'UTC'
    formatted_datetime = ' '.join([dt_date, dt_time, dt_tz])
    return jinja2.Markup('<time datetime="%s" class="jstime" \
                           data-format="%s">%s</time>'
                 % (formatted_datetime, format, formatted_datetime))


@register.function
def date_now():
    return datetime.datetime.utcnow()
