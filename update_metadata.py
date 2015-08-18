#!/usr/bin/env python

import urllib
import urllib2
import json
import settings

def get_url(url, token=None, data=None, info=False, method='GET'):
    headers = { 'Content-type': 'application/json' }

    if token:
        headers['X-Auth-Token'] = token

    request = urllib2.Request(url, data, headers)
    if method != 'GET':
        request.get_method = lambda: method
    response = urllib2.urlopen(request)

    if info:
        return response.info()
    else:
        return response.read()

def get_token():
    data = {
        'auth': {
            'identity': {
                'methods': ['password'],
                'password': {
                    'user': {
                        'domain': {
                            'name': 'Default'
                        },
                        'name': settings.ADMIN_USERNAME,
                        'password': settings.ADMIN_PASSWORD
                    }
                }
            },
            'scope': {
                'project': {
                    'domain': {
                        'name': 'Default'
                    },
                    'name': 'admin'
                }
            }
        }
    }
    response = get_url('%s/auth/tokens' % settings.OS_AUTH_URL, data=json.dumps(data), info=True)
    token = response.getheader('X-Subject-Token')
    if not token:
        raise Exception('Auth token not created correctly!')
    return token

def get_new_idps_from_sp():
    response = get_url('%s' % settings.DISCO_URL)
    response_data = json.loads(response)
    new_idps = [idp['entityID'] for idp in response_data]

    if len(new_idps) == 0:
        raise Exception('No IdP could be retrieved from SP discofeed url.')

    return new_idps

def delete_old_idps(token):
    response = get_url('%s/OS-FEDERATION/identity_providers' % settings.OS_AUTH_URL, token=token)
    response_data = json.loads(response)
    if not response_data['identity_providers']:
        return

    get_url('%s/OS-FEDERATION/identity_providers/%s' % (settings.OS_AUTH_URL, settings.FEDERATION_ID), token=token, method='DELETE')

    response = get_url('%s/OS-FEDERATION/identity_providers' % settings.OS_AUTH_URL, token=token)
    response_data = json.loads(response)
    if response_data['identity_providers']:
        raise Exception('Identity providers not deleted correctly!')

def register_new_idps(token, new_idps):
    data = {
        'identity_provider': { 
            'description': 'IdPs of the %s federation' % settings.FEDERATION_ID,
            'remote_ids': new_idps, 
            'enabled': True
        } 
    }

    get_url('%s/OS-FEDERATION/identity_providers/%s' % (settings.OS_AUTH_URL, settings.FEDERATION_ID), token=token, data=json.dumps(data), method='PUT')

    response = get_url('%s/OS-FEDERATION/identity_providers' % settings.OS_AUTH_URL, token=token)
    response_data = json.loads(response)
    if not response_data['identity_providers']:
        raise Exception('Identity providers not created correctly!')

def add_idp_protocols(token):
    data = {
        'protocol': {
            'mapping_id': settings.MAPPING_ID
        }
    }

    get_url('%s/OS-FEDERATION/identity_providers/%s/protocols/%s' % (settings.OS_AUTH_URL, settings.FEDERATION_ID, settings.PROTOCOL_ID), token=token, data=json.dumps(data), method='PUT')

def update_metadata():
    print 'Obtain all new IdPs from Discofeed...',
    new_idps = get_new_idps_from_sp()
    print ' done!'

    print 'Retrieve a token to be used for authentication...',
    token = get_token()
    print ' done!'

    print 'Delete previously created IdPs...',
    delete_old_idps(token)
    print ' done!'

    print 'Register all new IdP entityIDs in the federation module of keystone...',
    register_new_idps(token, new_idps)
    print ' done!'

    print 'Add the protocol to manage SAML requests...',
    add_idp_protocols(token)
    print ' done!'

if __name__ == '__main__':
    update_metadata()
