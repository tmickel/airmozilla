import datetime

from django.shortcuts import render


def page(request, template='main/home.html'):
    """Main view."""
    current_date = datetime.datetime.utcnow()
    return render(request, template, {'current_date': current_date})
