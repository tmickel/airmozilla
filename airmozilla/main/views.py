from django.core.paginator import Paginator, PageNotAnInteger, EmptyPage
from django.shortcuts import get_object_or_404, redirect, render

from airmozilla.main.models import Event, Participant


def page(request, template):
    """Base page:  renders templates bare, used for static pages."""
    featured = Event.objects.filter(public=True, featured=True)
    return render(request, template, {'featured': featured})


def home(request, page=1):
    """Home renders paginated recent videos."""
    featured = Event.objects.filter(public=True, featured=True)
    if request.user.is_active:
        events = Event.objects.filter().order_by('-end_time')
    else:
        events = Event.objects.filter(public=True).order_by('-end_time')
    paginate = Paginator(events, 10)
    try:
        events_paged = paginate.page(page)
    except PageNotAnInteger:
        events_paged = paginate.page(1)
    except EmptyPage:
        events_paged = paginate.page(paginate.num_pages)
    return render(request, 'main/home.html', {'events': events_paged,
                                              'featured': featured})


def event(request, slug):
    """Event video view page."""
    featured = Event.objects.filter(public=True, featured=True)
    event = get_object_or_404(Event, slug=slug)

    if not event.public and not request.user.is_active:
        return redirect('main:login')

    return render(request, 'main/event.html', {'event': event, 
                                               'featured': featured})


def participant(request, slug):
    """View an individual participant/speaker profile."""
    participant = get_object_or_404(Participant, slug=slug)
    featured = Event.objects.filter(public=True, featured=True)
    if participant.cleared != 'Y':
        return redirect('main:login')
    return render(request, 'main/participant.html', 
                           {'participant': participant, 'featured': featured})
