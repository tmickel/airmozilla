from airmozilla.main.models import Event

def sidebar(request):
    featured = Event.objects.approved().filter(public=True, featured=True)
    upcoming = Event.objects.upcoming().order_by('start_time')
    if not request.user.is_active:
        featured = featured.filter(public=True)
        upcoming = upcoming.filter(public=True)
    upcoming = upcoming[:3]
    return {
        'upcoming': upcoming,
        'featured': featured
    }
