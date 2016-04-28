from os import environ

from django.http import HttpResponse
from django.shortcuts import redirect
from django.shortcuts import render_to_response
from django.conf import settings
from django.template import loader
import sys


import requests
import json

import utils
import logging


logger = logging.getLogger('openstack_regsite')

def _get_attrs(request):
    eppn = request.META.get(settings.SHIBBOLETH_NAME_ATTRIBUTE, None)
    entitlement = request.META.get(settings.SHIBBOLETH_ENTITLEMENT_ATTRIBUTE, None)
    email = request.META.get(settings.SHIBBOLETH_EMAIL_ATTRIBUTE, None)

    return eppn, entitlement, email
    
def _update_user(request):
    pw = None
    eppn, entitlement, email = _get_attrs(request)
    next_page = request.GET.get('return', '/')
    if request.method == "POST":
        pw = request.POST.get('password')
    username = utils.update_user(username=eppn, entitlement=entitlement, mail=email, password=pw)
    #redirect to the Shibboleth HOOK return url.
    return redirect(next_page)

def _show_user_creation_page(request):
    eppn, entitlement, email = _get_attrs(request)
    shibboleth_entitlement = utils.parse_entitlements(entitlement)
    if shibboleth_entitlement is not None:
        shibboleth_entitlement = dict(shibboleth_entitlement)
    else:
        shibboleth_entitlement = ["You are not authorized for any projects."]
    attributes = {
        'openstack_servername': settings.OPENSTACK_NAME,
        'openstack_url': settings.OPENSTACK_URL,
        'openstack_keystone': settings.OPENSTACK_KEYSTONE_ADMIN_URL,
        'shibboleth_name': eppn,
        'shibboleth_entitlement': shibboleth_entitlement,
        'return': request.GET.get('return', '/'),
        'target': request.GET.get('target', None),
        'base_url': settings.BASE_URL,
    }

    return render_to_response('regsite/index.html', attributes)

def _deprovision_hook(request):

    if request.method == "POST":
        hook_json = json.loads(request.body)
        if 'key' in hook_json.keys() and  hook_json['key'] == settings.SHIBBOLETH_HOOK_KEY:
            if hook_json['action'] == 'attribute_change':
                for eppn in hook_json['data']:
                    entitlement = None
                    for attribute in hook_json['data'][eppn]:
                        if attribute == settings.SHIBBOLETH_ENTITLEMENT_ID:
                            for attr_value in hook_json['data'][eppn][attribute]:
                                if entitlement is None:
                                    entitlement = attr_value
                                else:
                                    entitlement += ';' + attr_value
                    username = utils.update_user(username=eppn, entitlement=entitlement)
                return HttpResponse(username)
            if hook_json['action'] == 'user_removed':
                for eppn in hook_json['data']:
                    username = utils.update_user(username=eppn, entitlement=None)
                return HttpResponse(username)
 
def index(request):
    eppn, entitlement, email = _get_attrs(request)
    
    if eppn is None:
        return render_to_response('regsite/missing_attribute.html', {'message': settings.MISSING_EPPN_MESSAGE})
    if entitlement is None and not utils.user_exists(eppn):
        return render_to_response('regsite/missing_attribute.html', {'message': settings.MISSING_ENTITLEMENT_MESSAGE})

    if not settings.USER_ACCEPT_CREATION or utils.user_exists(eppn):
        return _update_user(request)
    else:
        return _show_user_creation_page(request)

def shib_hook(request):
    return _update_user(request=request)

def deprovision(request):
    return _deprovision_hook(request)
