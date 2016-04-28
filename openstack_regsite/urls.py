from django.contrib import admin
from django.conf.urls import patterns, include, url
from django.conf.urls.static import static
from django.conf import settings

urlpatterns = patterns('views',
    url(r'^$', 'index'),
    url(r'^shib_hook$', 'shib_hook'),
    url(r'^deprovision$', 'deprovision'),
)

urlpatterns += static(settings.STATIC_URL, document_root=settings.STATIC_ROOT)
