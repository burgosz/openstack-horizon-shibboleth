from django.conf.urls import patterns, include, url
from django.contrib import admin
import openstack_regsite

urlpatterns = patterns('openstack_regsite.views',
    url(r'^$', 'shib_hook'),
)
