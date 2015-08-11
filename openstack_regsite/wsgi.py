"""
WSGI config for openstack_regsite project.

It exposes the WSGI callable as a module-level variable named ``application``.

For more information on this file, see
https://docs.djangoproject.com/en/1.7/howto/deployment/wsgi/
"""

import os, sys
current_directory = os.path.dirname(__file__)
sys.path.append(current_directory)

import settings
activate_this = os.path.join('%s/bin/activate_this.py' % settings.VEVN_DIR)
execfile(activate_this, dict(__file__=activate_this))

os.environ.setdefault('DJANGO_SETTINGS_MODULE', 'settings')
from django.core.wsgi import get_wsgi_application
application = get_wsgi_application()

