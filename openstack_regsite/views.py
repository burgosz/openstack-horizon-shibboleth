from os import environ

from django.http import HttpResponse
from django.shortcuts import redirect
from django.shortcuts import render_to_response
from django.conf import settings

import requests
import json

import utils
import logging

logger = logging.getLogger('openstack_regsite')

def _update_user(request):
    next_page = request.GET.get('return', '/')
    eppn = request.META.get(settings.SHIBBOLETH_NAME_ATTRIBUTE, None)
    if not eppn:
        logger.error("Name attribute is missing!")
        raise Exception("Missing name attribute.")

    entitlement = request.META.get(settings.SHIBBOLETH_ENTITLEMENT_ATTRIBUTE, None)
    if entitlement is not None:
        username = utils.update_user(request)

    #redirect to the Shibboleth HOOK return url.
    return redirect(next_page)

def _show_user_creation_page(request):
    attributes = {
        'openstack_servername': settings.OPENSTACK_NAME,
        'openstack_url': settings.OPENSTACK_URL,
        'openstack_keystone': settings.OPENSTACK_KEYSTONE_ADMIN_URL,
        'shibboleth_name': request.META.get(settings.SHIBBOLETH_NAME_ATTRIBUTE, None),
        'shibboleth_entitlement': dict(utils.get_entitlemets(request)),
        'return': request.GET.get('return', '/'),
        'target': request.GET.get('target', None),
        'base_url': settings.BASE_URL,
    }

    return render_to_response('regsite/index.html', attributes)

def index(request):
    eppn = request.META.get(settings.SHIBBOLETH_NAME_ATTRIBUTE, None)
    if not settings.USER_ACCEPT_CREATION or utils.user_exists(eppn):
        return _update_user(request)
    else:
        return _show_user_creation_page(request)

def shib_hook(request):
    return _update_user(request)
