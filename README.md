# Shibboleth authentication plugin for Openstack Horizon

Using this plugin Openstack Horizon can authenticate users via Shibboleth.<br>
Features
  - User authentication
  - User creation
  - Project creation
  - Role creation
  - Access control based on Shibboleth provided attributes

### How it works
When Shibboleth authenticates the user it write the required attributes to Apache enviroment variables, then the django.wsgi passes them to the plugin which authenticates the user at Keystone and then creates an user object for the Django backend.

If the user not exists in the Keystone database, the plugin creates it. The plugin can assign the users to projects with the provided role. The plugin creates the project and the role if not exists.

The backend will generate a password for the user which can be used for API and cli usage. This password can be checked in /horizon/auth/get_password/ url.
### Installation
Download the openstack_auth_shib dictionary into your Python libraries.<br>
On Ubuntu:
```sh
/usr/lib/python2.7/dist-packages/openstack_auth_shib
```
Download the files from openstack-dashboard into your openstack-dashboard folder, and ovverride the files.
On Ubuntu by default:
```sh
/usr/share/openstack-dashboard/openstack-dashboard
```
Add the following lines to your openstack-dashboard local_settings.py file:
```sh
AUTHENTICATION_BACKENDS = ('openstack_auth_shib.backend.Shib_KeystoneBackend',)
OPENSTACK_KEYSTONE_URL ="location of Keystone url"
OPENSTACK_KEYSTONE_ADMIN_URL = "location of Keystone admin url (similar to OPENSTACK_KEYSTONE_URL)"
OPENSTACK_KEYSTONE_ADMIN_TOKEN = "your keystone admin token"
SHIB_PASSWORD_SALT = "random number" This will be used to SALT the username to provide a password for cli usage.
SHIB_LOGOUT = "url of Shibboleth logout page"
```
### Apache configuration
You must protect the Horizon page with Shibboleth.
### Shibboleth configuration
Shibboleth must map the username provided via your attribute provider to <b>eppn.</b><br>
The roles and project names must be in the <b>entitlement</b> attribute. The entitlement postfix contains the project and role name separeted with colon: <i>entilement_prefix:<b>project:role</b></i>.<br>
The email address of the user will be assigned based on the <b>mail</b> attribute.

If no entitlement or eppn provided the user can't login.
