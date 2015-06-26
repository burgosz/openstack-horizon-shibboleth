# Licensed under the Apache License, Version 2.0 (the "License");
# you may not use this file except in compliance with the License.
# You may obtain a copy of the License at
#
#    http://www.apache.org/licenses/LICENSE-2.0
#
# Unless required by applicable law or agreed to in writing, software
# distributed under the License is distributed on an "AS IS" BASIS,
# WITHOUT WARRANTIES OR CONDITIONS OF ANY KIND, either express or
# implied.
# See the License for the specific language governing permissions and
# limitations under the License.

import logging

import django
import json
import requests
from django.conf import settings
from django.contrib import auth
from django.contrib.auth.decorators import login_required  # noqa
from django.contrib.auth import views as django_auth_views
from django.contrib.auth import login as auth_login
from django.contrib.auth import authenticate
from django import shortcuts
from django.utils import functional
from django.utils import http
from django.views.decorators.cache import never_cache  # noqa
from django.views.decorators.csrf import csrf_protect  # noqa
from django.views.decorators.debug import sensitive_post_parameters  # noqa

from keystoneclient import exceptions as keystone_exceptions
from keystoneclient.v2_0 import client as keystone_client_v2

from openstack_auth import forms
# This is historic and is added back in to not break older versions of
# Horizon, fix to Horizon to remove this requirement was committed in
# Juno
from openstack_auth.forms import Login  # noqa
from openstack_auth import user as auth_user
from openstack_auth import utils
from openstack_auth_shib import shib_utils
from openstack_auth import exceptions

try:
    is_safe_url = http.is_safe_url
except AttributeError:
    is_safe_url = utils.is_safe_url


LOG = logging.getLogger(__name__)


@sensitive_post_parameters()
@csrf_protect
@never_cache
def login(request, template_name=None, extra_context=None, **kwargs):
    """Logs a user in using the :class:`~openstack_auth.forms.Login` form."""
    # If the user is already authenticated, redirect them to the
    # dashboard straight away, unless the 'next' parameter is set as it
    # usually indicates requesting access to a page that requires different
    # permissions.
    if not request.user.is_authenticated():
        eppn = request.META.get(settings.SHIBBOLETH_NAME_FIELD, None)
        if not eppn:
           raise Exception('Missing parameters in user session')

        auth_url = getattr(settings,'OPENSTACK_KEYSTONE_URL')
        domain = getattr(settings,'OPENSTACK_KEYSTONE_DEFAULT_DOMAIN','Default')
        username = shib_utils.update_user(request)
        password = shib_utils.get_password(request, username)

        LOG.debug("Authenticating username=%s, password=%s, user_domain_name=%s, auth_url=%s" % (username, password, domain, auth_url))
        user = authenticate(request=request, username=username, password=password, user_domain_name=domain, auth_url=auth_url)
        msg = 'Login successful for user "%(username)s".' % {'username': username}
        LOG.info(msg)

        res = auth_login(request, user)
        # Set the session data here because django's session key rotation will erase it if we set it earlier.
        LOG.info("Token id: " + request.user.token.id)

        if request.user.is_authenticated():
            auth_user.set_session_from_user(request, request.user)
            regions = dict(forms.Login.get_region_choices())
            region = request.user.endpoint
            region_name = regions.get(region)
            request.session['region_endpoint'] = region
            request.session['region_name'] = region_name

    return shortcuts.redirect(settings.LOGIN_REDIRECT_URL)

@never_cache
def get_password(request):
    username = request.user.username
    password = shib_utils.get_password(request, username)
    return shortcuts.render(request,'password.html',{"password":password})

