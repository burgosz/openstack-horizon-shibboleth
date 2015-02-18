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

""" Module defining the Django auth backend class for the Keystone API. """
import openstack_auth

import logging

from django.conf import settings
from django.utils.translation import ugettext_lazy as _

from keystoneclient import exceptions as keystone_exceptions

from openstack_auth import exceptions
from openstack_auth import user as auth_user
from openstack_auth import utils
from openstack_auth import exceptions


LOG = logging.getLogger(__name__)


KEYSTONE_CLIENT_ATTR = "_keystoneclient"

class Shib_KeystoneBackend(openstack_auth.backend.KeystoneBackend):
   
    def authenticate(self, request=None, token=None, username=None, password=None,
                     user_domain_name=None, auth_url=None):
        """Authenticates a user via the Keystone Identity API."""
        LOG.info('Beginning user authentication for user "%s".' % username)

        insecure = getattr(settings, 'OPENSTACK_SSL_NO_VERIFY', False)
        ca_cert = getattr(settings, "OPENSTACK_SSL_CACERT", None)
        endpoint_type = getattr(
            settings, 'OPENSTACK_ENDPOINT_TYPE', 'publicURL')

        # keystone client v3 does not support logging in on the v2 url any more
        if utils.get_keystone_version() >= 3:
            if utils.has_in_url_path(auth_url, "/v2.0"):
                LOG.warning("The settings.py file points to a v2.0 keystone "
                            "endpoint, but v3 is specified as the API version "
                            "to use. Using v3 endpoint for authentication.")
                auth_url = utils.url_path_replace(auth_url, "/v2.0", "/v3", 1)

        keystone_client = utils.get_keystone_client()
        try:
            client = keystone_client.Client(
                username=username,
                password=password,
                auth_url=auth_url,
                insecure=insecure,
                cacert=ca_cert,
                debug=settings.DEBUG)

            unscoped_auth_ref = client.auth_ref
            unscoped_token = auth_user.Token(auth_ref=unscoped_auth_ref)
        except (keystone_exceptions.Unauthorized,
                keystone_exceptions.Forbidden,
                keystone_exceptions.NotFound) as exc:
            msg = _('Invalid user name or password.')
            LOG.debug(str(exc))
            raise exceptions.KeystoneAuthException(msg)
        except (keystone_exceptions.ClientException,
                keystone_exceptions.AuthorizationFailure) as exc:
            msg = _("An error occurred authenticating. "
                    "Please try again later.")
            LOG.debug(str(exc))
            raise exceptions.KeystoneAuthException(msg)

        # Check expiry for our unscoped auth ref.
        self.check_auth_expiry(unscoped_auth_ref)

        # Check if token is automatically scoped to default_project
        if unscoped_auth_ref.project_scoped:
            auth_ref = unscoped_auth_ref
        else:
            # For now we list all the user's projects and iterate through.
            try:
                if utils.get_keystone_version() < 3:
                    projects = client.tenants.list()
                else:
                    client.management_url = auth_url
                    projects = client.projects.list(
                        user=unscoped_auth_ref.user_id)
            except (keystone_exceptions.ClientException,
                    keystone_exceptions.AuthorizationFailure) as exc:
                msg = _('Unable to retrieve authorized projects.')
                raise exceptions.KeystoneAuthException(msg)

            # Abort if there are no projects for this user
            if not projects:
                msg = _('You are not authorized for any projects.')
                raise exceptions.KeystoneAuthException(msg)

            while projects:
                project = projects.pop()
                try:
                    client = keystone_client.Client(
                        tenant_id=project.id,
                        token=unscoped_auth_ref.auth_token,
                        auth_url=auth_url,
                        insecure=insecure,
                        cacert=ca_cert,
                        debug=settings.DEBUG)
                    auth_ref = client.auth_ref
                    break
                except (keystone_exceptions.ClientException,
                        keystone_exceptions.AuthorizationFailure):
                    auth_ref = None

            if auth_ref is None:
                msg = _("Unable to authenticate to any available projects.")
                raise exceptions.KeystoneAuthException(msg)

        # Check expiry for our new scoped token.
        self.check_auth_expiry(auth_ref)

        # If we made it here we succeeded. Create our User!
        user = auth_user.create_user_from_token(
            request,
            auth_user.Token(auth_ref),
            client.service_catalog.url_for(endpoint_type=endpoint_type))

        if request is not None:
            request.session['unscoped_token'] = unscoped_token.id
            request.user = user

            # Support client caching to save on auth calls.
            setattr(request, KEYSTONE_CLIENT_ATTR, client)

        LOG.debug('Authentication completed for user "%s".' % username)
        return user