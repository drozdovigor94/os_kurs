#!/usr/bin/python

# GNU General Public License v3.0+ (see COPYING or https://www.gnu.org/licenses/gpl-3.0.txt)

ANSIBLE_METADATA = {
    'metadata_version': '1.1',
    'status': ['preview'],
    'supported_by': 'community'
}

DOCUMENTATION = '''
---
module: my_module

short_description: Module to configure and run route.py

version_added: "0.1"

description:
    - This module sets up route.py config file according to routers data passed through arguments
      and runs route.py if it somehow have changed the config file

options:
    route_py_path:
        description:
            - Path to route.py module
        required: true
    config_path:
        description:
            - Path to route.py config file
        required: true
    global_login:
        description:
            - Global login for route.py
        required: true
    global_password:
        description:
            - Global password for route.py
        required: true
    routers:
        description:
            - List of routers, each element is a dict with keys 'ip', 'login', 'password'
        required: false

author:
    - Ekaterina Belyaeva
'''

EXAMPLES = '''
# Refer to playbook
'''

RETURN = '''
msg:
    description: Message describing the result
    type: str
route_py_output:
    description: Output (stdout) of running route.py
    type: str
'''

from ansible.module_utils.basic import AnsibleModule
import os
import csv


def run_module():

    # define input arguments format
    module_args = dict(
        route_py_path=dict(type='str', required=True),
        config_path=dict(type='str', required=True),
        global_username=dict(type='str', required=True),
        global_password=dict(type='str', required=True),
        run_route_py=dict(type='bool', required=False, default=True),
        routers=dict(type='list', elements='dict', required=False,
            options=dict(ip=dict(type='str', required=True),
                         username=dict(type='str', required=False, default=''),
                         password=dict(type='str', required=False, default='')))
    )   

    #define returned result format
    result = dict(
        changed=False,
        msg='',
        route_py_output='',
    )

    module = AnsibleModule(
        argument_spec=module_args,
        supports_check_mode=False
    )

    # Check if we have no routers to add - then just finish module
    if module.params['routers'] == None:
        result['msg'] = 'No routers were specified'
        module.exit_json(**result)

    fieldnames = ['#ip', 'username', 'password']

    # Try to open config file or create if it doesn't exist
    # and set up csv reader and writer
    try:
        config_file = open(module.params['config_path'], 'r+', newline='')
        writer = csv.DictWriter(config_file, fieldnames=fieldnames)
        reader = csv.DictReader(config_file)
    except FileNotFoundError:
        config_file = open(module.params['config_path'], 'w+', newline='')
        writer = csv.DictWriter(config_file, fieldnames=fieldnames)
        writer.writeheader()
        reader = csv.DictReader(config_file)

    # Get list of existing routers and their ip's in particular
    existing_routers = list(reader)
    existing_routers_ips = [router['#ip'] for router in existing_routers]

    # change 'ip' key to '#ip' in new routers (so it follows required by route.py format)
    new_routers = module.params['routers']
    for router in new_routers:
        router['#ip'] = router.pop('ip')

    # Check what routers are not in config file and add them
    add_count = 0
    for router in new_routers:
        if router['#ip'] not in existing_routers_ips:
            result['changed'] = True
            add_count = add_count + 1
            writer.writerow(router)

    #close config file
    config_file.close()

    result['msg'] = "Existing routers: {}, new routers: {}, added {} routers".format(len(existing_routers), len(new_routers), add_count)

    #result['msg'] = [existing_routers, new_routers]
    
    # Run route.py if new routers were added
    if result['changed'] == True and module.params['run_route_py']:
        route_py_exists = os.path.isfile(module.params['route_py_path'])
        if route_py_exists:
            res = module.run_command(['python3', 
                module.params['route_py_path'], 
                module.params['global_username'], 
                module.params['global_password'], 
                module.params['config_path']])
            if res[0] != 0:
                result['msg'] = 'route.py failed with code {}'.format(res[0])
                module.fail_json(**result)
            result['route_py_output'] = res[1]
        else:
            result['msg'] = 'route.py not found'
            module.fail_json(**result)

    module.exit_json(**result)

def main():
    run_module()

if __name__ == '__main__':
    main()
