from django.shortcuts import render

from airmozilla.main.models import Event


def home(request, template='main/home.html'):
    """Main view."""
    e = Event.objects.filter()[0]  # demonstration of TZ tools
    return render(request, template, {'event': e})
