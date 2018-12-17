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

def run_module():

    # define input arguments format
    module_args = dict(
        route_py_path=dict(type='str', required=True),
        config_path=dict(type='str', required=True),
        global_login=dict(type='str', required=True),
        global_password=dict(type='str', required=True),
        run_route_py=dict(type='bool', required=False, default=True),
        routers=dict(type='list', elements='dict', required=False),
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

    # Try to open config file and get list of routers
    try:
        config_file = open(module.params['config_path'], 'r')
        config_file.next()
        existing_routers = [line.rstrip('\n') for line in config_file]
        config_file.close()

    except:
        existing_routers = []

    # Format specified routers for route.py config
    new_routers = [x['ip'] + ', ' + x['login'] + ', ' + x['password'] for x in module.params['routers']]

    # Check what routers are not in config file and add them
    add_count = 0
    with open(module.params['config_path'], 'a+') as config_file:
        for router in new_routers:
            if router not in existing_routers:
                result['changed'] = True
                add_count = add_count + 1
                config_file.write(router + '\n')

    result['msg'] = "Existing routers: {}, new routers: {}, added {} routers".format(len(existing_routers), len(new_routers), add_count)

    result['msg'] = [existing_routers, new_routers]

    # Run route.py if new routers were added
    if result['changed'] == True and module.params['run_route_py']:
        route_py_exists = os.path.isfile(module.params['route_py_path'])
        if route_py_exists:
            res = module.run_command(['python3', 
                module.params['route_py_path'], 
                module.params['global_login'], 
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
