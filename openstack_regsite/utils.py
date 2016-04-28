from django.conf import settings
import logging
from collections import defaultdict
from keystoneclient.v3 import client as keystone_client
from keystoneclient.auth.identity import v3
from keystoneclient import session

LOG = logging.getLogger(__name__)

#admin_token = getattr(settings, 'OPENSTACK_KEYSTONE_ADMIN_TOKEN')
keystone_user = getattr(settings, 'OPENSTACK_KEYSTONE_USER')
keystone_password = getattr(settings, 'OPENSTACK_KEYSTONE_PASSWORD')
keystone_user_project = getattr(settings, 'OPENSTACK_KEYSTONE_USER_PROJECT')
admin_url = getattr(settings, 'OPENSTACK_KEYSTONE_ADMIN_URL')
name_field = getattr(settings, 'SHIBBOLETH_NAME_ATTRIBUTE', 'eppn')
mail_field = getattr(settings, 'SHIBBOLETH_EMAIL_ATTRIBUTE', 'mail')
entitlement_field = getattr(settings, 'SHIBBOLETH_ENTITLEMENT_ATTRIBUTE', 'entitlement')
default_domain = getattr(settings, 'DEFAULT_DOMAIN_NAME', 'Default')


def admin_client():
    endpoint = admin_url
    auth = v3.Password(auth_url=admin_url,
                       username=keystone_user,
                       password=keystone_password,
                       user_domain_id='default',
                       project_name=keystone_user_project,
                       project_domain_id='default'
                      )
    sess = session.Session(auth=auth)
    client = keystone_client.Client(session=sess)
    return client

def get_user(username):
    client = admin_client()
    userlist = client.users.list()
    for user in userlist:
        if user.name == username:
            return user
    return None

def get_role(name):
    client = admin_client()
    roles = client.roles.list()
    for role in roles:
        if role.name == name:
            return role
    return None

def get_tenant(name):
    client = admin_client()
    tenants = client.projects.list()
    for tenant in tenants:
        if tenant.name == name:
            return tenant
    return None

def parse_entitlements(entitlement):
    if entitlement is None:
        return None
    entitlement_list = entitlement.split(';')
    ent_roles = defaultdict(list)
    # retrieve info from shibboleth session
    for entitlement in entitlement_list:
        entitlement = entitlement.strip(':')
        splitted = entitlement.split(":")
        rolename = splitted[len(splitted)-1]
        tenantname = splitted[len(splitted)-2]
        ent_roles[tenantname].append(rolename)
    LOG.debug("entitlement = %s" % entitlement)
    LOG.debug("ent_roles = %s" % ent_roles)
    return ent_roles

def create_tenants(client, tenant_list):
    new_tenants = list()
    for t in tenant_list:
        tenant = get_tenant(t)
        if tenant is None:
            LOG.info("Creating tenant %s." % t)
            client.projects.create(name=t, domain=default_domain)
        new_tenants.append(tenant)
    return new_tenants

def create_roles(client, role_list):
    for rolename in role_list:
        role = get_role(rolename)
        if role is None:
            client.roles.create(rolename)

def update_roles(entitlement, user):
    client = admin_client()
    ent_roles = parse_entitlements(entitlement)
    if ent_roles is not None:
        create_tenants(client, ent_roles.keys())
        role_list = [ent_roles[r] for r in ent_roles.keys()]
        role_list = reduce(lambda x, y: x+y, role_list)
        create_roles(client, role_list)
    existing_tenants = client.projects.list()
    for tenant in existing_tenants:
        # Check roles for the current tenant
        for role in client.roles.list(user=user, project=tenant):
            # If the tenant is not in the ent_roles, it is an old tenant, all
            # roles will be removed from user.
            # If the role in keystone is a correct role for the user, remove
            # this value from ent_roles.
            if (ent_roles is not None and
                tenant.name in ent_roles and
                role.name in ent_roles[tenant.name]):

                ent_roles[tenant.name].remove(role.name)
            # Otherwise, if the role in keystone is not correct, revoke the role
            # from the user.
            else:
                client.roles.revoke(role, user=user, project=tenant)
    # Create remaining roles in the ent_roles dict.
    if ent_roles is not None:
        for tenant in existing_tenants:
            if tenant.name in ent_roles:
                for rolename in ent_roles[tenant.name]:
                    role = get_role(rolename)
                    client.roles.grant(role, user=user, project=tenant)

def update_mail(user, email):
    client = admin_client()
    client.users.update(user, email=email)

def create_user(username, password):
    client = admin_client()
    newuser = client.users.create(name=username, domain=default_domain, password=password)
    return newuser

def user_exists(username):
    if settings.TEST:
        return False

    user = get_user(username)
    return user is not None

def update_user(username, entitlement, mail=None, password=None):
    if settings.TEST:
        return username

    user = get_user(username)

    if user is None:
        LOG.info("Creating user %s." % username)
        user = create_user(username, password)

    update_roles(entitlement, user)
    if mail is not None:
        update_mail(user, mail)

    return user.name
