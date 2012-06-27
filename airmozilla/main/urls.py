from django.conf.urls.defaults import *

from . import views


urlpatterns = patterns('',
    url(r'^$', views.page, name='home'),
    url(r'^login/$', views.page, name='login',
        kwargs={'template':'main/login.html'}),
    url(r'^about/$', views.page, name='about',
        kwargs={'template':'main/about.html'}),

)
