# Shibboleth authentication plugin for Openstack

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
Usually the SP configuration for this regsite must be shared with the configuration for Keystone. For this reason the configuration of regsite usually happens
in the samle file where the keystone webapplication is configured within Apache.

Here an example of configuration for Apache:
```apache
<VirtualHost *:5000>
    SSLEngine on
    SSLProtocol all -SSLv2
    SSLCipherSuite HIGH:MEDIUM:!aNULL:!MD5
    SSLCertificateFile /etc/httpd/ssl/os-test.mi.garr.it.crt
    SSLCertificateKeyFile /etc/httpd/ssl/os-test.mi.garr.it.key
    SSLCertificateChainFile /etc/httpd/ssl/CA_GARR_MI.pem

    <Location /Shibboleth.sso>
        SetHandler shib
    </Location>

    Alias /regsite/static /opt/openstack-horizon-shibboleth/openstack_regsite/static

    <Directory /opt/openstack-horizon-shibboleth/openstack_regsite/static>
        Require all granted
    </Directory>

    WSGIDaemonProcess regsite home=/opt/openstack-horizon-shibboleth/openstack_regsite
    WSGIProcessGroup regsite
    WSGIPassAuthorization Off
    WSGIScriptAlias /regsite /opt/openstack-horizon-shibboleth/openstack_regsite/wsgi.py

    <Directory /opt/openstack-horizon-shibboleth/openstack_regsite>
        Options all
        AllowOverride all
        Require all granted
    </Directory>

    <Location /regsite>
        authtype shibboleth
        shibRequestSetting requireSession 1
        require valid-user
    </Location>

    WSGIDaemonProcess keystone-public processes=5 threads=1 user=keystone display-name=%{GROUP}
    WSGIProcessGroup keystone-public
    WSGIScriptAlias / /var/www/cgi-bin/keystone/main
    WSGIApplicationGroup %{GLOBAL}
    WSGIPassAuthorization On
    <IfVersion >= 2.4>
      ErrorLogFormat "%{cu}t %M"
    </IfVersion>
    ErrorLog /var/log/httpd/keystone.log
    CustomLog /var/log/httpd/keystone_access.log combined

    <Location /v3/auth/OS-FEDERATION/websso/saml2>
        authtype shibboleth
        shibRequestSetting requireSession 1
        require valid-user
    </Location>

</VirtualHost>
```

### Shibboleth configuration
Shibboleth must map the username provided via your attribute provider to <b>eppn</b>.<br>
The roles and project names might be in the <b>entitlement</b> or <b>isMemberOf</b> attribute. This is also configurable.
This field must contain the project and role name separeted with colon: <i>entilement_prefix:<b>project:role</b></i>.<br>
The email address of the user will be assigned based on the <b>mail</b> attribute.
If no entitlement or eppn provided the user can't login.

The Shibboleth SP must also be configured to invoke the post login hook that creates users/projects on keystone.
This configuration consist on adding ``sessionHook="/regsite"`` to the ``ApplicationDefaults`` tag of the ``/etc/shibboleth/shibboleth2.xml`` file.


### OpenStack keystone and horizon configuration
To propertly configure keystone and horizon components of OpenStack to work correctly with federated access and with the regsite described in this projects, the following configurations need to be done.a

Firstly the ``openstack/django_openstack_auth`` project must be of a verion including the patch to the change id Change-Id: Ib5c99e3b7b16bfb64b651d2129643d6f53fe7722
(more information on it can be found [on the official openstack review site](https://review.openstack.org/#/c/173669/).
If he version of the project does not include this patch, it must be applied by hand with the followin commands:
```sh
$ cd /usr/lib/python2.7/site-packages/openstack_auth
$ patch -p1 < /opt/openstack-horizon-shibboleth/Ib5c99e3b7b16bfb64b651d2129643d6f53fe7722.patch
```

The file ``/etc/keystone/keystone.conf`` must be modified as follows (only modified parts presented, all the rest of the file remains untouched):
```ini
[DEFAULT]
...
public_endpoint = https://os.server.name:5000

[auth]
...
methods = external,password,token,oauth1,saml2
saml2 = keystone.auth.plugins.mapped.Mapped

[federation]
...
remote_id_attribute = 'Shib-Identity-Provider'
remote_id_attribute = 'Shib-Identity-Provider'
trusted_dashboard = https://os.server.name/dashboard/auth/websso/
sso_callback_template = /etc/keystone/sso_callback_template.html

[ssl]
...
enable=True
```

Then the following commands needs to be executed to create the right structures inside keystone via the JSON API:
```sh
#!/bin/bash
OS_AUTH_URL='https://os.server.name:5000/v3'

# Retrieve a token to be used for authentication.
# The token-request.json file contains username/password for the admin user to authenticate with keystone.
export TOKEN=`curl -si -d @token-request.json -H "Content-type: application/json" http://localhost:35357/v3/auth/tokens | awk '/X-Subject-Token/ {print $2}'`

# IDs and constants to be used in curl scripts
FEDERATION_ID='federationid'
PROTOCOL_ID='saml2'
MAPPING_ID='shib'
ENTITY_IDS='"https://idp.mi.garr.it/idp/shibboleth"'

# Register IdPs entityID in the federation module of keystone
curl -si -H"X-Auth-Token:$TOKEN" -H "Content-type: application/json" -X PUT -d "{ \"identity_provider\": { \"description\": \"IdPs of the $FEDERATION_ID federation\", \"remote_ids\": [ $ENTITY_IDS ], \"enabled\": true } }" $OS_AUTH_URL/OS-FEDERATION/identity_providers/$FEDERATION_ID

# Print identity_providers to see if everything's ok
#curl -si -H"X-Auth-Token:$TOKEN" -H "Content-type: application/json" -X GET $OS_AUTH_URL/OS-FEDERATION/identity_providers

# Add the protocol to manage SAML requests
curl -si -H"X-Auth-Token:$TOKEN" -H "Content-type: application/json" -X PUT -d "{ \"protocol\": { \"mapping_id\": \"$MAPPING_ID\" } }" $OS_AUTH_URL/OS-FEDERATION/identity_providers/$FEDERATION_ID/protocols/$PROTOCOL_ID

# Add the mapping
curl -si -H"X-Auth-Token:$TOKEN" -H "Content-type: application/json" -X PUT -d "{ \"mapping\": { \"rules\": [ { \"local\": [ { \"user\": { \"domain\": { \"id\": \"default\" }, \"type\": \"local\", \"name\": \"{0}\" } } ], \"remote\": [ { \"type\": \"eppn\" } ] } ] } } " $OS_AUTH_URL/OS-FEDERATION/mappings/$MAPPING_ID
```

Lastly the ``/etc/openstack-dashboard/local_settings`` horizon config file must be edited as follows (only modified parts presented, all the rest of the file remains untouched):
```ini
OPENSTACK_KEYSTONE_URL = "https://os.server.name:5000/v3"
...
OPENSTACK_API_VERSIONS = {
    "identity": 3,
}

# Enables keystone web single-sign-on if set to True.
WEBSSO_ENABLED = True

# Determines which authentication choice to show as default.
WEBSSO_INITIAL_CHOICE = "saml2"

WEBSSO_CHOICES = (
    ("credentials", _("Keystone Credentials")),
#    ("oidc", _("OpenID Connect")),
    ("saml2", _("Security Assertion Markup Language"))) 
```
