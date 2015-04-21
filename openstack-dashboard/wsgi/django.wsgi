import logging
import os
import sys
from django.core.wsgi import get_wsgi_application
from django.conf import settings

# Add this file path to sys.path in order to import settings
sys.path.insert(0, os.path.join(os.path.dirname(os.path.realpath(__file__)), '../..'))
os.environ['DJANGO_SETTINGS_MODULE'] = 'openstack_dashboard.settings'
sys.stdout = sys.stderr

sys.path.append("/usr/share/openstack-dashboard/")

DEBUG = False

_application = get_wsgi_application()
env_variables_to_pass = ['eppn', 'entitlement','mail',]
def application(environ, start_response):
    # pass the WSGI environment variables on through to os.environ
    for var in env_variables_to_pass:
        os.environ[var] = environ.get(var, '')
    return _application(environ, start_response)
