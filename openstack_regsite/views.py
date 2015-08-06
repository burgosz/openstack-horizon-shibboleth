from os import environ

from django.http import HttpResponse
from django.shortcuts import redirect
from django.conf import settings
from django.shortcuts import render_to_response

import requests
import json

import utils
import logging

logger = logging.getLogger('openstack_regsite')

def index(request):

    attributes = {
        'openstack_servername': settings.OPENSTACK_NAME,
        'openstack_url': settings.OPENSTACK_URL,
        'openstack_keystone': settings.OPENSTACK_KEYSTONE_ADMIN_URL,
        'shibboleth_name': request.META.get(settings.SHIBBOLETH_NAME_ATTRIBUTE, None),
        'shibboleth_entitlement': request.META.get(settings.SHIBBOLETH_ENTITLEMENT_ATTRIBUTE, None),
    }

    return render_to_response('regsite/index.html', attributes)

def shib_hook(request):
    eppn = request.META.get(settings.SHIBBOLETH_NAME_ATTRIBUTE, None)
    if not eppn:
        logger.error("Name attribute is missing!")
        raise Exception("Missing name attribute.")

    entitlement = request.META.get(settings.SHIBBOLETH_ENTITLEMENT_ATTRIBUTE, None)
    if entitlement is not None:
        username = utils.update_user(request)
    #redirect to the Shibboleth HOOK return url.
    return redirect(request.GET['return'])
