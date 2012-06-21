from django.shortcuts import render

from airmozilla.main.models import Event


def home(request, template='main/home.html'):
    """Main view."""
    return render(request, template)
