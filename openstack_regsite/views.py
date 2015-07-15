from django.http import HttpResponse
from os import environ
from django.shortcuts import redirect
from django.conf import settings
import requests, json
from openstack_regsite import utils
from openstack_regsite import logger


def shib_hook(request):
    eppn = request.META.get(settings.SHIBBOLETH_NAME_ATTRIBUTE, None)
    if not eppn:
        logger.log("Name attribute is missing!")
        raise Exception("Missing name attribute.")

    entitlement = request.META.get(settings.SHIBBOLETH_ENTITLEMENT_ATTRIBUTE, None)
    if entitlement is not None:
        username = utils.update_user(request)
    #redirect to the Shibboleth HOOK return url.
    return redirect(request.GET['return'])
