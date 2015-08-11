# Shibboleth authentication plugin for Openstack Horizon

Using this plugin Openstack Horizon can authenticate users via Shibboleth.<br>
Features
  - User authentication
  - User creation
  - Project creation
  - Role creation
  - Access control based on Shibboleth provided attributes

### How it works
To permit federated users to access OpenStack in a transparent way, the following main components are involved:
* The authentication submodule keystone needs to be configured as a Service Provider to a federation.
  This can be done activating the "federation" module of keystone.
* A webpage needs to be created to manage user/project creation, this page will operate as a standalone "signup page" web app (working title: regsite).
  This registration page can be automatically invoked after user login with a specific "post login" hook provided by the Shibboleth SP.
* Horizon needs to authenticate users with a web-SSO profile, usually provided by Shibboleth SP. 

The backend will generate a password for the user which can be used for API and cli usage. This password can be checked in /horizon/auth_shib/get_password/ url.

### Installation
This installation procedure describes how to configure the "regsite" Django application.
This installation procedure has been developed on Ubuntu Linux (14.04 LTS) but should work on any linux distro with relatively small changes.

On Ubuntu Linux 14.04 the necessary software that needs to be installed before this procedure could take care of the rest is:
* libffi-dev 
* python-virtualenv 
* apache2 
* libapache2-mod-wsgi
* libapabhe2-mod-shib

To install, then, download this git repository to a location of your choice, for instance in /opt:
```sh
$ cd /opt
$ git clone https://github.com/burgosz/openstack-horizon-shibboleth
```

Create a virtualenv that will contain all the files, libraries and modules used by this web page and then activate it:
```sh
$ cd /opt/openstack-horizon-shibboleth
$ virtualenv regsite-venv
$ source regsite-venv/bin/activate
```

Install all required python dependencies for this django application:
```sh
$ cd /opt/openstack-horizon-shibboleth/openstack_regsite
$ python setup.py develop
```

Copy the ``settings.py.example`` file to a file named ``settings.py`` and then edit it:
```sh
$ cd /opt/openstack-horizon-shibboleth/openstack_regsite
$ cp settings.py.example settings.py
$ vim settings.py
```

The importart parts of the file to be configured for your installation are
```sh
OPENSTACK_NAME = 'OpenStack for GN4 phase 1 project'       # Name of the OpenStack, shown to user for information
OPENSTACK_URL = 'https://openstack.gent.org'               # URL of the OpenStack instace (Horizon interface)
OPENSTACK_KEYSTONE_ADMIN_URL = 'http://10.1.12.4:35357/v3' # Admin URL of keystone, to be used for user/project creation
OPENSTACK_KEYSTONE_ADMIN_TOKEN = 'd1410ad0ab162c016171'    # Admin token used to authenticate to Keystone for user/project creation
SHIBBOLETH_NAME_ATTRIBUTE = 'eppn'                         # Attribute to be used as the username after login
SHIBBOLETH_ENTITLEMENT_ATTRIBUTE = 'entitlement'           # Attribute to be used for project/role definition after login
SHIBBOLETH_EMAIL_ATTRIBUTE = 'mail'                        # Attribute to be used as the email of the user after login
DEFAULT_DOMAIN_NAME = 'Default'                            # Default domain name to be set after login
USER_ACCEPT_CREATION = True                                # Flag indicating wether to show a confirmation screen before user/project creation
```

### Apache configuration
You must protect the Horizon page with Shibboleth, you also have to specify the configuration of ``mod_wsgi`` to operate the django application.
Here an example of configuration for Apache:
```apache
Alias /static /opt/openstack-horizon-shibboleth/openstack_regsite/static

<Directory /opt/openstack-horizon-shibboleth/openstack_regsite/static>
        Require all granted
</Directory>

WSGIDaemonProcess openstack home=/opt/openstack-horizon-shibboleth/openstack_regsite
WSGIProcessGroup openstack

WSGIScriptAlias / /opt/openstack-horizon-shibboleth/openstack_regsite/wsgi.py

<Directory /opt/openstack-horizon-shibboleth/openstack_regsite>
        Options all
        AllowOverride all
        Require all granted
</Directory>

<Location /shib_hook >
        authtype shibboleth
        shibRequestSetting requireSession 1
        require valid-user
</Location>
```

### Shibboleth configuration
Shibboleth must map the username provided via your attribute provider to <b>eppn</b>.<br>
The roles and project names must be in the <b>entitlement</b> or <b>isMemberOf</b> attribute.
This field must contain the project and role name separeted with colon: <i>entilement_prefix:<b>project:role</b></i>.<br>
The email address of the user will be assigned based on the <b>mail</b> attribute.
If no entitlement or eppn provided the user can't login.

The Shibboleth SP must also be configured to invoke the post login hook that creates users/projects on keystone.
This configuration consist on adding ``sessionHook="/regsite"`` to the ``ApplicationDefaults`` tag of the ``/etc/shibboleth/shibboleth2.xml`` file.
