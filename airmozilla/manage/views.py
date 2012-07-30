import pytz
import re

from django.conf import settings
from django.contrib.auth.decorators import (permission_required,
                                            user_passes_test)
from django.contrib.auth.models import User, Group
from django.core.mail import EmailMessage
from django.shortcuts import render, redirect, get_object_or_404
from django.utils import timezone

from funfactory.urlresolvers import reverse
from jinja2 import Environment, meta

from airmozilla.base.utils import json_view, paginate, tz_apply, unique_slugify
from airmozilla.main.models import (Approval, Category, Event, EventOldSlug,
                                    Location, Participant, Tag, Template)
from airmozilla.manage import forms

staff_required = user_passes_test(lambda u: u.is_staff)


def _process_form(request, form_class, instance, template, redirect_view,
                  pre_save=None, render_form=None):
    """Returns a page response for boilerplate Django model form processing.
       If a form is successful, the instance is updated appropriately.
       pre_save(instance, form) and render_form(form) are optional callbacks
       to modify the instance before submission and modify the form before
       rendering.  Callbacks return the modified object (instance or form)."""
    if request.method == 'POST':
        if 'cancel' in request.POST:
            return redirect(redirect_view)
        form = form_class(request.POST, request.FILES or None,
                          instance=instance)
        if form.is_valid():
            if pre_save:
                pre_instance = form.save(commit=False)
                pre_instance = pre_save(pre_instance, form)
                pre_instance.save()
                form.save_m2m()
            else:
                form.save()
            return redirect(redirect_view)
    else:
        form = form_class(instance=instance)
    if render_form:
        form = render_form(form)
    return render(request, template, {'form': form, 'instance': instance})


@staff_required
def home(request):
    """Management home page / explanation page."""
    return render(request, 'manage/home.html')


@staff_required
@permission_required('change_user')
def users(request):
    """User editor:  view users and update a user's group."""
    if request.method == 'POST':
        form = forms.UserFindForm(request.POST)
        if form.is_valid():
            user = User.objects.get(email=form.cleaned_data['email'])
            return redirect('manage:user_edit', user.id)
    else:
        form = forms.UserFindForm()
    users_paged = paginate(User.objects.all(), request.GET.get('page'), 10)
    return render(request, 'manage/users.html',
                  {'paginate': users_paged, 'form': form})


@staff_required
@permission_required('change_user')
def user_edit(request, id):
    """Editing an individual user."""
    user = User.objects.get(id=id)
    return _process_form(request, forms.UserEditForm, user,
                         'manage/user_edit.html', 'manage:users')


@staff_required
@permission_required('change_group')
def groups(request):
    """Group editor: view groups and change group permissions."""
    groups = Group.objects.all()
    return render(request, 'manage/groups.html', {'groups': groups})


@staff_required
@permission_required('change_group')
def group_edit(request, id):
    """Edit an individual group."""
    group = Group.objects.get(id=id)
    return _process_form(request, forms.GroupEditForm, group,
                         'manage/group_edit.html', 'manage:groups')


@staff_required
@permission_required('add_group')
def group_new(request):
    """Add a new group."""
    group = Group()
    return _process_form(request, forms.GroupEditForm, group,
                         'manage/group_new.html', 'manage:groups')


@staff_required
@permission_required('add_event')
def event_request(request):
    """Event request page:  create new events to be published."""
    def pre_save_event_request(event, form):
        if not event.slug:
            event.slug = unique_slugify(event.title, [Event, EventOldSlug],
                                        event.start_time.strftime('%Y%m%d'))
        tz = pytz.timezone(request.POST['timezone'])
        event.start_time = tz_apply(event.start_time, tz)
        if event.archive_time:
            event.archive_time = tz_apply(event.archive_time, tz)
        event.creator = request.user
        event.modified_user = request.user
        return event
    instance = Event() if request.method == 'POST' else None
    return _process_form(request, forms.EventRequestForm, instance,
                         'manage/event_request.html', 'manage:home',
                         pre_save_event_request)


@staff_required
@permission_required('change_event')
def events(request):
    """Event edit/production:  approve, change, and publish events."""
    search_results = []
    if request.method == 'POST':
        search_form = forms.EventFindForm(request.POST)
        if search_form.is_valid():
            search_results = Event.objects.filter(
                title__icontains=search_form.cleaned_data['title']
            ).order_by('-start_time')
    else:
        search_form = forms.EventFindForm()
    initiated = Event.objects.initiated().order_by('start_time')
    upcoming = Event.objects.upcoming().order_by('start_time')
    live = Event.objects.live().order_by('start_time')
    archiving = Event.objects.archiving().order_by('-archive_time')
    archived = Event.objects.archived().order_by('-archive_time')
    archived_paged = paginate(archived, request.GET.get('page'), 10)
    return render(request, 'manage/events.html', {
        'initiated': initiated,
        'upcoming': upcoming,
        'live': live,
        'archiving': archiving,
        'paginate': archived_paged,
        'form': search_form,
        'search_results': search_results
    })


@staff_required
@permission_required('change_event')
def event_edit(request, id):
    """Edit form for a particular event."""
    event = Event.objects.get(id=id)
    old_slug = event.slug

    def pre_save_event_edit(event, form):
        if not event.slug:
            event.slug = unique_slugify(event.title,
                                        [Event, EventOldSlug],
                                        event.start_time.strftime('%Y%m%d'))
        if event.slug != old_slug:
            EventOldSlug.objects.create(slug=old_slug, event=event)
        tz = pytz.timezone(request.POST['timezone'])
        event.start_time = tz_apply(event.start_time, tz)
        if event.archive_time:
            event.archive_time = tz_apply(event.archive_time, tz)
        approvals_old = [app.group for app in event.approval_set.all()]
        approvals_new = form.cleaned_data['approvals']
        approvals_add = set(approvals_new).difference(approvals_old)
        approvals_remove = set(approvals_old).difference(approvals_new)
        for approval in approvals_add:
            group = Group.objects.get(name=approval)
            app = Approval(group=group, event=event)
            app.save()
            emails = [u.email for u in group.user_set.all()]
            subject = ('[Air Mozilla] Approval requested: "%s"' %
                       event.title)
            message = ('A new event has been created that requires'
                       ' approval from someone in your group (%s). Please log'
                       ' in to the Air Mozilla management page (%s) to review'
                       ' the request.\n\nTitle: %s\nCreator: %s\nDate and time'
                       ': %s\n Description: %s' %
                       (group.name,
                        request.build_absolute_uri(
                            reverse('manage:approvals')
                        ),
                        event.title, event.creator.email, event.start_time,
                        event.description))
            email = EmailMessage(subject, message,
                                 settings.EMAIL_FROM_ADDRESS, emails)
            email.send()
        for approval in approvals_remove:
            app = Approval.objects.get(group=approval, event=event)
            app.delete()
        event.modified_user = request.user
        return event

    def render_form_event_edit(form):
        timezone.activate(pytz.timezone('UTC'))
        tag_format = lambda objects: ','.join(map(unicode, objects))
        participants_formatted = tag_format(event.participants.all())
        tags_formatted = tag_format(event.tags.all())
        form.initial['participants'] = participants_formatted
        form.initial['tags'] = tags_formatted
        form.initial['timezone'] = timezone.get_current_timezone()
        return form

    return _process_form(request, forms.EventEditForm, event,
                         'manage/event_edit.html', 'manage:events',
                         pre_save_event_edit, render_form_event_edit)


@staff_required
@permission_required('add_event')
@json_view
def tag_autocomplete(request):
    """ Feeds JSON tag names to the Event Request form. """
    query = request.GET['q']
    tags = Tag.objects.filter(name__istartswith=query)[:5]
    tag_names = [{'id': t.name, 'text': t.name} for t in tags]
    # for new tags - the first tag is the query
    tag_names.insert(0, {'id': query, 'text': query})
    return {'tags': tag_names}


@staff_required
@permission_required('add_event')
@json_view
def participant_autocomplete(request):
    """ Participant names to Event Request autocompleter. """
    query = request.GET['q']
    participants = Participant.objects.filter(name__icontains=query)
    # Only match names with a component which starts with the query
    regex = re.compile(r'\b%s' % re.escape(query.split()[0]), re.I)
    participant_names = [{'id': p.name, 'text': p.name}
                         for p in participants if regex.findall(p.name)]
    return {'participants': participant_names[:5]}


@staff_required
@permission_required('change_participant')
def participants(request):
    """Participants page:  view and search participants/speakers. """
    if request.method == 'POST':
        search_form = forms.ParticipantFindForm(request.POST)
        if search_form.is_valid():
            participants = Participant.objects.filter(
                name__icontains=search_form.cleaned_data['name']
            )
        else:
            participants = Participant.objects.all()
    else:
        participants = Participant.objects.all()
        search_form = forms.ParticipantFindForm()
    participants_paged = paginate(participants, request.GET.get('page'), 10)
    return render(request, 'manage/participants.html',
                  {'paginate': participants_paged, 'form': search_form})


@staff_required
@permission_required('change_participant')
def participant_edit(request, id):
    """ Participant edit page:  update biographical info. """
    participant = Participant.objects.get(id=id)
    if 'sendmail' in request.POST:
        redirect_view = 'manage:participant_email'
    else:
        redirect_view = 'manage:participants'

    def pre_save_participant_edit(participant, form):
        if not participant.slug:
            participant.slug = unique_slugify(participant.name, [Participant])
        return participant
    return _process_form(request, forms.ParticipantEditForm, participant,
                         'manage/participant_edit.html', redirect_view,
                         pre_save_participant_edit)


@staff_required
@permission_required('change_participant')
def participant_email(request, id):
    participant = Participant.objects.get(id=id)
    to_addr = participant.email
    from_addr = settings.EMAIL_FROM_ADDRESS
    reply_to = request.user.email
    if not reply_to:
        reply_to = from_addr
    last_events = (Event.objects.filter(participants=participant)
                        .order_by('-created'))
    last_event = last_events[0] if last_events else None
    cc_addr = last_event.creator.email if last_event else None
    subject = ('Presenter profile on Air Mozilla (%s)' % participant.name)
    profile_url = request.build_absolute_uri(
        reverse('main:participant', kwargs={'slug': participant.slug})
    )
    message = ('A new profile for you will be added to the Air'
               ' Mozilla website (http://air.mozilla.org) to be shown along'
               ' with events and presentations you participate in.  Please'
               ' verify the information posted is correct; if there are any'
               ' issues or corrections, please let us know'
               ' (%s).\n\nProfile: %s' % (reply_to, profile_url))
    if request.method == 'POST':
        if 'submit' in request.POST:
            cc = [cc_addr] if (('cc' in request.POST) and cc_addr) else None
            email = EmailMessage(subject, message, from_addr, [to_addr],
                                 cc=cc, headers={'Reply-To': reply_to})
            email.send()
        return redirect('manage:participants')
    else:
        return render(request, 'manage/participant_email.html',
                      {'participant': participant, 'message': message,
                       'subject': subject, 'reply_to': reply_to,
                       'to_addr': to_addr, 'from_addr': from_addr,
                       'cc_addr': cc_addr, 'last_event': last_event})


@staff_required
@permission_required('add_participant')
def participant_new(request):
    def pre_save_participant_new(participant, form):
        if not participant.slug:
            participant.slug = unique_slugify(participant.name, [Participant])
        return participant
    return _process_form(request, forms.ParticipantEditForm, Participant(),
                         'manage/participant_new.html', 'manage:participants',
                         pre_save_participant_new)


@staff_required
@permission_required('change_category')
def categories(request):
    categories = Category.objects.all()
    if request.method == 'POST':
        form = forms.CategoryForm(request.POST, instance=Category())
        if form.is_valid():
            form.save()
            form = forms.CategoryForm()
    else:
        form = forms.CategoryForm()
    return render(request, 'manage/categories.html',
                  {'categories': categories, 'form': form})


@staff_required
@permission_required('change_template')
@json_view
def template_env_autofill(request):
    template_id = request.GET['template']
    template = Template.objects.get(id=template_id)
    env = Environment()
    ast = env.parse(template.content)
    undeclared_variables = list(meta.find_undeclared_variables(ast))
    var_templates = ["%s=" % v for v in undeclared_variables]
    return {'variables':  '\n'.join(var_templates)}


@staff_required
@permission_required('change_template')
def templates(request):
    templates = Template.objects.all()
    return render(request, 'manage/templates.html', {'templates': templates})


@staff_required
@permission_required('change_template')
def template_edit(request, id):
    template = Template.objects.get(id=id)
    return _process_form(request, forms.TemplateEditForm, template,
                         'manage/template_edit.html', 'manage:templates')


@staff_required
@permission_required('add_template')
def template_new(request):
    return _process_form(request, forms.TemplateEditForm, Template(),
                         'manage/template_new.html', 'manage:templates')


@staff_required
@permission_required('remove_template')
def template_remove(request, id):
    if request.method == 'POST':
        template = Template.objects.get(id=id)
        template.delete()
    return redirect('manage:templates')


@staff_required
@permission_required('change_location')
def locations(request):
    locations = Location.objects.all()
    return render(request, 'manage/locations.html', {'locations': locations})


@staff_required
@permission_required('change_location')
def location_edit(request, id):
    location = Location.objects.get(id=id)
    return _process_form(request, forms.LocationEditForm, location,
                         'manage/location_edit.html', 'manage:locations')


@staff_required
@permission_required('add_location')
def location_new(request):
    return _process_form(request, forms.LocationEditForm, Location(),
                         'manage/location_new.html', 'manage:locations')


@staff_required
@permission_required('change_location')
def location_remove(request, id):
    if request.method == 'POST':
        location = Location.objects.get(id=id)
        location.delete()
    return redirect('manage:locations')


@staff_required
@json_view
def location_timezone(request):
    location = get_object_or_404(Location, id=request.GET['location'])
    return {'timezone': location.timezone}


@staff_required
@permission_required('change_approval')
def approvals(request):
    user = request.user
    approvals = Approval.objects.filter(group__in=user.groups.all(),
                                        processed=False)
    recent = (Approval.objects.filter(group__in=user.groups.all(),
                                      processed=True)
                      .order_by('-processed_time')[:25])
    return render(request, 'manage/approvals.html', {'approvals': approvals,
                                                     'recent': recent})


@staff_required
@permission_required('change_approval')
def approval_review(request, id):
    approval = Approval.objects.get(id=id)
    if approval.group not in request.user.groups.all():
        return redirect('manage:approvals')
    if request.method == 'POST':
        form = forms.ApprovalForm(request.POST, instance=approval)
        approval = form.save(commit=False)
        approval.approved = 'approve' in request.POST
        approval.processed = True
        approval.user = request.user
        approval.save()
        return redirect('manage:approvals')
    else:
        form = forms.ApprovalForm(instance=approval)
    return render(request, 'manage/approval_review.html',
                  {'approval': approval, 'form': form})
