from django.shortcuts import render

from airmozilla.main.models import Event


def page(request, template):
    """Base page:  renders templates bare, used for static pages."""
    return render(request, template)


def home(request):
    """Home renders paginated recent videos."""
    events = Event.objects.filter()
    return render(request, 'main/home.html', {'events': events})
