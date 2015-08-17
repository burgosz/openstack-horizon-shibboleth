#!/usr/bin/env python

import urllib
import urllib2
import json

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

def get_token(config):
    data = {
        'auth': {
            'identity': {
                'methods': ['password'],
                'password': {
                    'user': {
                        'domain': {
                            'name': 'Default'
                        },
                        'name': config['admin_username'],
                        'password': config['admin_password']
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
    response = get_url('%s/auth/tokens' % config['os_auth_url'], data=json.dumps(data), info=True)
    token = response.getheader('X-Subject-Token')
    if not token:
        raise Exception('Auth token not created correctly!')
    return token

def get_new_idps_from_sp(config):
    response = get_url('%s' % config['disco_url'])
    response_data = json.loads(response)
    new_idps = [idp['entityID'] for idp in response_data]

    if len(new_idps) == 0:
        raise Exception('No IdP could be retrieved from SP discofeed url.')

    return new_idps

def delete_old_idps(config, token):
    response = get_url('%s/OS-FEDERATION/identity_providers' % config['os_auth_url'], token=token)
    response_data = json.loads(response)
    if not response_data['identity_providers']:
        return

    get_url('%s/OS-FEDERATION/identity_providers/%s' % (config['os_auth_url'], config['federation_id']), token=token, method='DELETE')

    response = get_url('%s/OS-FEDERATION/identity_providers' % config['os_auth_url'], token=token)
    response_data = json.loads(response)
    if response_data['identity_providers']:
        raise Exception('Identity providers not deleted correctly!')

def register_new_idps(config, token, new_idps):
    data = {
        'identity_provider': { 
            'description': 'IdPs of the %s federation' % config['federation_id'],
            'remote_ids': new_idps, 
            'enabled': True
        } 
    }

    get_url('%s/OS-FEDERATION/identity_providers/%s' % (config['os_auth_url'], config['federation_id']), token=token, data=json.dumps(data), method='PUT')

    response = get_url('%s/OS-FEDERATION/identity_providers' % config['os_auth_url'], token=token)
    response_data = json.loads(response)
    if not response_data['identity_providers']:
        raise Exception('Identity providers not created correctly!')

def add_idp_protocols(config, token):
    data = {
        'protocol': {
            'mapping_id': config['mapping_id']
        }
    }

    get_url('%s/OS-FEDERATION/identity_providers/%s/protocols/%s' % (config['os_auth_url'], config['federation_id'], config['protocol_id']), token=token, data=json.dumps(data), method='PUT')

def update_metadata(config):
    print 'Obtain all new IdPs from Discofeed...',
    new_idps = get_new_idps_from_sp(config)
    print ' done!'

    print 'Retrieve a token to be used for authentication...',
    token = get_token(config)
    print ' done!'

    print 'Delete previously created IdPs...',
    delete_old_idps(config, token)
    print ' done!'

    print 'Register all new IdP entityIDs in the federation module of keystone...',
    register_new_idps(config, token, new_idps)
    print ' done!'

    print 'Add the protocol to manage SAML requests...',
    add_idp_protocols(config, token)
    print ' done!'

if __name__ == '__main__':
    update_metadata({
        'os_auth_url': 'http://10.20.30.49:35357/v3',
        'disco_url': 'https://os-test.mi.garr.it/Shibboleth.sso/DiscoFeed',
        'admin_username': 'admin',
        'admin_password': '391fab406dff4474',
        'federation_id': 'Idem',
        'protocol_id': 'saml2',
        'mapping_id': 'shib',
    })
