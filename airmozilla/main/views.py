import datetime

from django.core.paginator import Paginator, PageNotAnInteger, EmptyPage
from django.shortcuts import get_object_or_404, redirect, render

from airmozilla.main.models import Event, Participant


def page(request, template):
    """Base page:  renders templates bare, used for static pages."""
    featured = Event.objects.filter(public=True, featured=True)
    return render(request, template, {'featured': featured})


def home(request, page=1):
    """Paginated recent videos and live videos."""
    featured = Event.objects.filter(public=True, featured=True)
    now = datetime.datetime.utcnow()
    if request.user.is_active:
        past_events = (Event.objects.filter(end_time__lt=now, status='S')
                           .order_by('-end_time'))
        live_events = (Event.objects.filter(end_time__gt=now, 
                            start_time__lt=now, status='S')
                            .order_by('-end_time'))
    else:
        past_events = (Event.objects.filter(public=True, end_time__lt=now,
                            status='S')
                           .order_by('-end_time'))
        live_events = (Event.objects.filter(end_time__gt=now, 
                            start_time__lt=now, status='S', public=True)
                            .order_by('-end_time'))
    paginate = Paginator(past_events, 10)
    try:
        past_events_paged = paginate.page(page)
    except PageNotAnInteger:
        past_events_paged = paginate.page(1)
    except EmptyPage:
        past_events_paged = paginate.page(paginate.num_pages)
    live = False
    also_live = []
    if live_events:
        live = live_events[0]
        also_live = live_events[1:]
    return render(request, 'main/home.html', {
        'events': past_events_paged,
        'featured': featured,
        'live': live,
        'also_live': also_live
    })


def event(request, slug):
    """Video, description, and other metadata."""
    featured = Event.objects.filter(public=True, featured=True)
    event = get_object_or_404(Event, slug=slug)
    if ((not event.public or event.status == 'I') 
        and not request.user.is_active):
        return redirect('main:login')
    return render(request, 'main/event.html', {
        'event': event, 
        'featured': featured,
    })


def participant(request, slug):
    """Individual participant/speaker profile."""
    participant = get_object_or_404(Participant, slug=slug)
    featured = Event.objects.filter(public=True, featured=True)
    if participant.cleared != 'Y':
        return redirect('main:login')
    return render(request, 'main/participant.html', {
        'participant': participant,
        'featured': featured
    })
