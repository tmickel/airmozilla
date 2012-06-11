from django.contrib.admin.views.decorators import staff_member_required
from django.contrib.auth.decorators import permission_required
from django.contrib.auth.models import User
from django.shortcuts import render, redirect

from airmozilla.manage.forms import UserEditForm

@staff_member_required
def home(request):
    """Management homepage / explanation page."""
    return render(request, 'home.html')

@staff_member_required
@permission_required('change_user')
def user_edit(request):
    """User editor:  view users and update a user's group."""
    users = User.objects.all() 
    return render(request, 'user_edit.html', {'users': users})

@staff_member_required
@permission_required('change_user')
def user_edit_form(request, id):
    """Editing an individual user."""
    user = User.objects.get(id=id)
    if request.method == 'POST':
        form = UserEditForm(request.POST, instance=user)
        if form.is_valid():
            form.save()
            return redirect('manage.user_edit')
    else:
        form = UserEditForm(instance=user)
    return render(request, 'user_edit_form.html', {'form': form, 'u': user})

@staff_member_required
@permission_required('change_group')
def group_edit(request):
    """Group editor: view groups and change group permissions."""
    return render(request, 'group_edit.html')

@staff_member_required
@permission_required('manage.event_request')
def event_request(request):
    """Event request page:  create new events to be published."""
    return render(request, 'event_request.html')

@staff_member_required
@permission_required('manage.participant_edit')
def participant_edit(request):
    """Participant editor page:  update biographical info."""
    return render(request, 'participant_edit.html')

@staff_member_required
@permission_required('manage.produce_events')
def event_edit(request):
    """Event edit/production:  change, approve, publish events."""
    return render(request, 'event_edit.html')
