#!/usr/bin/python

ANSIBLE_METADATA = {
    'metadata_version': '1.1',
    'status': ['preview'],
    'supported_by': 'community'
}

DOCUMENTATION = '''
---
module: syno_reverse_proxy

short_description: Manages reverse proxy entries in Synology DSM.

description: >
  Manages reverse proxy entries in Synology DSM. Same as can be configured in
  the web UI under 'Control Panel > Application Portal > Reverse Proxy'.

options:
	name:
		description: >
		  Name of the reverse proxy entry. Used as an indentifier.
	backend:
		description: Endpoint to direct traffic to.
		options:
			fqdn:
				description: Hostname.
			port:
				description: Port number.
			https:
				description: Whether to use https.
	frontend:
		description: Frontend parameters.
		options:
			fqdn:
				description: Hostname.
			port:
				description: Port number. Defaults to 80 or 443.
			https:
				description: Whether to use https.
	customize_headers:
		description: Customize headers param.
'''

EXAMPLES = r'''
- name: 'Add a reverse proxy for DSM itself'
  syno_reverse_proxy:
    name: "DSM"
    backend:
      fqdn: "localhost"
      port: 5000
    frontend:
      fqdn: "dsm.my.local.network"
      https: yes
    customize_headers:
      - name: "Upgrade"
        value: "$http_upgrade"
      - name: "Connection"
        value: "$connection_upgrade"
'''

from ansible.module_utils.api import SynoAPIModule

def lookup(d, path):
	for name in path.split('.'):
		if d is None:
			return None
		d = d.get(name)
	return d

def list_different(list1: list, list2: list):
    list1 = list1 or []
    list2 = list2 or []
    diff = [i for i in list1 + list2 if i not in list1 or i not in list2]
    return len(diff) != 0

def run_module():
    module_args = dict(
    	name=dict(type='str', required=True),
    	backend=dict(type='dict', required=True, options=dict(
    		fqdn=dict(type='str', required=True),
    		port=dict(type='int', required=True),
    		https=dict(type='bool', default=False),
		)),
    	frontend=dict(type='dict', required=True, options=dict(
    		fqdn=dict(type='str', required=True),
    		port=dict(type='int', required=False),
    		https=dict(type='bool', default=False),
		)),
    	customize_headers=dict(type='list', element='dict', default=[], options=dict(
    		name=dict(type='string', required=True),
    		value=dict(type='string', required=True),
		)),
    )
    result = dict(changed=False, diff=dict(before=dict(), after=dict()))
    module = SynoAPIModule(argument_spec=module_args, supports_check_mode=True)

    configured_entry = dict(
    	description=module.params['name'],
    	backend=dict(
    		fqdn=module.params['backend']['fqdn'],
    		port=module.params['backend']['port'],
    		protocol=1 if module.params['backend']['https'] else 0,
    	),
    	frontend=dict(
    		fqdn=module.params['frontend']['fqdn'],
    		protocol=1 if module.params['frontend']['https'] else 0,
    		port=module.params['frontend'].get('port'),
    	),
    )
    if configured_entry['frontend']['port'] is None:
    	https = module.params['frontend']['https']
    	configured_entry['frontend']['port'] = 443 if https else 80

    if module.params.get('customize_headers', None):
    	configured_entry['customize_headers']=module.params['customize_headers']

    _, existing_data = module.syno_web_api('SYNO.Core.AppPortal.ReverseProxy',
    									   'list')

    existing_entry = None
    for entry in existing_data['entries']:
    	if entry['description'] == module.params['name']:
    		if existing_entry:
    			module.fail_json(msg=(
    				'Found more than one existing entry matching description. '
    				'Please rename one of them manually.'))
    		existing_entry = entry

    if existing_entry:
    	configured_entry['UUID'] = existing_entry['UUID']

    result['diff']['after'].update(dict(present=True))
    result['diff']['after'].update(configured_entry)

    if existing_entry:
    	result['diff']['before'].update(dict(present=True))
    	result['diff']['before'].update(existing_entry)
    else:
    	result['diff']['before'].update(dict(present=False))

    fields = [
    	'backend.fqdn',
    	'backend.port',
    	'backend.protocol',
    	'frontend.fqdn',
    	'frontend.port',
    	'frontend.protocol',
    ]
    for field in fields:
    	if lookup(existing_entry, field) != lookup(configured_entry, field):
    		result['changed'] = True

    if list_different(lookup(configured_entry, 'customize_headers'), lookup(existing_entry, 'customize_headers')):
	    result['changed'] = True

    if module.check_mode:
    	module.exit_json(**result)

    method = 'update' if existing_entry else 'create'
    module.syno_web_api('SYNO.Core.AppPortal.ReverseProxy',
    	method, dict(entry=configured_entry))

    module.exit_json(**result)

def main():
    run_module()


if __name__ == '__main__':
    main()
