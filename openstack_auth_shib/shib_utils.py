from django.conf import settings
import json
import requests
import logging
import hashlib
from openstack_auth import utils
from keystoneclient import exceptions as keystone_exceptions
from collections import defaultdict
from openstack_auth import exceptions

LOG = logging.getLogger(__name__)
admin_token = getattr(settings, 'OPENSTACK_KEYSTONE_ADMIN_TOKEN')
admin_url = getattr(settings, 'OPENSTACK_KEYSTONE_ADMIN_URL')
name_field = getattr(settings, 'SHIBBOLETH_NAME_FIELD', 'eppn')
mail_field = getattr(settings, 'SHIBBOLETH_EMAIL_FIELD', 'mail')
entitlement_field = getattr(settings, 'SHIBBOLETH_ENTITLEMENT_FIELD', 'entitlement')

def admin_client():
    endpoint = admin_url

    if utils.get_keystone_version() >= 3:
        if not utils.has_in_url_path(endpoint, '/v3'):
            endpoint = utils.url_path_replace(endpoint, '/v2.0', '/v3', 1)

    keystone_client = utils.get_keystone_client()
    client = keystone_client.Client(
        token = admin_token,
        endpoint = endpoint)

    return client

def get_user(request, username):
    client = admin_client()
    userlist = client.users.list()

    for user in userlist:
        if utils.get_keystone_version() >= 3 and user.name == username:
            return user
        elif utils.get_keystone_version() < 3 and user.username == username:
            return user
    return None

def get_password(request, username):
    salt = getattr(settings,'SHIB_PASSWORD_SALT')
    password = hashlib.sha512(username+salt).hexdigest()
    return password

def get_role(name):
    client = admin_client()
    roles = client.roles.list()
    for role in roles:
        if role.name == name:
            return role
    return None

def get_tenant(name):
    client = admin_client()
    if utils.get_keystone_version() >= 3:
        tenants = client.projects.list()
    else:
        tenants = client.tenants.list()
    for tenant in tenants:
        if tenant.name == name:
            return tenant
    return None

def update_roles(request, user):
    client = admin_client()
    entitlement = request.META.get(entitlement_field, '').replace("\\", "")
    entitlement_list = entitlement.split(';')
    ent_roles = defaultdict(list)

    # retrieve info from shibboleth session
    for entitlement in entitlement_list:
        splitted = entitlement.split(":")
        rolename = splitted[len(splitted)-1]
        tenantname = splitted[len(splitted)-2]
        ent_roles[tenantname].append(rolename)

    # create tenants
    new_tenants = list()
    for t in ent_roles.keys():
        tenant = get_tenant(t)
        if tenant is None:
            if utils.get_keystone_version() >= 3:
                tenants = client.projects.create(tenant_name=t)
            else:
                tenant = client.tenants.create(tenant_name=t)
        new_tenants.append(tenant)
    
    for r in ent_roles.keys():
        for rolename in ent_roles[r]:
            role = get_role(rolename)
            if role is None:
                client.roles.create(rolename)
    
    if utils.get_keystone_version() >= 3:
        # remove unused roles and add new ones
        existing_tenants = client.projects.list()
        for tenant in existing_tenants:
            for role in client.roles.list(user=user, project=tenant):
                client.roles.revoke(role, user=user, project=tenant)
        for tenant in new_tenants:
            for rolename in ent_roles[tenant.name]:
                role = get_role(rolename)
                client.roles.grant(role, user=user, project=tenant)
    else:
        # remove unused roles and add new ones
        existing_tenants = client.tenants.list()
        for tenant in existing_tenants:
            if (user in tenant.list_users()):
                roles = user.list_roles(tenant)
                for role in roles:
                    tenant.remove_user(user, role)
        for tenant in new_tenants:
            for rolename in ent_roles[tenant.name]:
                role = get_role(rolename)
                tenant.add_user(user, role)

def update_mail(request, user):
    client = admin_client()
    email = request.META.get(mail_field, None)
    client.users.update(user, email=email)

def update_password(request, user):
    client = admin_client()
    client.users.update(user, password=get_password(request, user.name))

def create_user(request, username):
    client = admin_client()
    newuser = client.users.create(name=username)
    return newuser

def update_user(request):
    username = request.META.get(name_field, None)
    user = get_user(request, username)
    if user is None:
        user = create_user(request, username)
    update_roles(request, user)
    update_password(request, user)
    update_mail(request, user)
    return user.name
