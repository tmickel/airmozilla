from django.conf.urls.defaults import *

from . import views


urlpatterns = patterns('',
    url(r'^manage/?$', views.home, name='manage.home'),
    url(r'^manage/users/(?P<id>\d+)$', views.user_edit_form, 
                             name='manage.user_edit_form'),
    url(r'^manage/users', views.user_edit, name='manage.user_edit'),
    url(r'^manage/groups', views.group_edit, name='manage.group_edit'),
    url(r'^manage/events/request', views.event_request, 
                                   name='manage.event_request'),
    url(r'^manage/events', views.event_edit, name='manage.event_edit'),
    url(r'^manage/participants', views.participant_edit, 
                                 name='manage.participant_edit'),
)
