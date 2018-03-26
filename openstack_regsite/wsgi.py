# Copyright 2015 Hungarian Academy of Sciences
#                Institute for Computer Science and Control
#
# Licensed under the Apache License, Version 2.0 (the "License");
# you may not use this file except in compliance with the License.
# You may obtain a copy of the License at
#
#     http://www.apache.org/licenses/LICENSE-2.0
#
# Unless required by applicable law or agreed to in writing, software
# distributed under the License is distributed on an "AS IS" BASIS,
# WITHOUT WARRANTIES OR CONDITIONS OF ANY KIND, either express or implied.
# See the License for the specific language governing permissions and
# limitations under the License.

"""
WSGI config for openstack_regsite project.

It exposes the WSGI callable as a module-level variable named ``application``.

For more information on this file, see
https://docs.djangoproject.com/en/1.7/howto/deployment/wsgi/
"""

import os, sys
current_directory = os.path.dirname(__file__)
sys.path.append(current_directory)

from openstack_dashboard import settings
if os.path.isdir('%s' % settings.VENV_DIR):
    activate_this = os.path.join('%s/bin/activate_this.py' % settings.VENV_DIR)
    execfile(activate_this, dict(__file__=activate_this))

os.environ.setdefault('DJANGO_SETTINGS_MODULE', 'openstack_dashboard.settings')
from django.core.wsgi import get_wsgi_application
application = get_wsgi_application()

