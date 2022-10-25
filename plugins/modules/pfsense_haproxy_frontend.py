#!/usr/bin/python
# -*- coding: utf-8 -*-

# Copyright: (c) 2019, Frederic Bor <frederic.bor@wanadoo.fr>
# GNU General Public License v3.0+ (see COPYING or https://www.gnu.org/licenses/gpl-3.0.txt)

from __future__ import absolute_import, division, print_function
import re
from ansible.module_utils.basic import AnsibleModule
from ansible_collections.pfsensible.core.plugins.module_utils.module_base import PFSenseModuleBase

__metaclass__ = type

ANSIBLE_METADATA = {'metadata_version': '1.1',
                    'status': ['preview'],
                    'supported_by': 'community'}

HAPROXY_FRONTEND_ADDR_ARGUMENT_SPEC=dict(
    addr=dict(required=True, type='str'),
    port=dict(required=True, type='int'),
    ssl=dict(required=False, type='bool'),
)

HAPROXY_FRONTEND_ARGUMENT_SPEC = dict(
    state=dict(default='present', choices=['present', 'absent']),
    name=dict(required=True, type='str'),
    descr=dict(required=True, type='str'),
    type=dict(required=True, choices=['tcp', 'ssl', 'http']),
    httpclose=dict(default='http-keep-alive', choices=['http-keep-alive', 'http-tunnel', 'httpclose', 'http-server-close', 'forceclose']),
    cert_descr=dict(default=None, type='str'),
    backend_serverpool=dict(default='', type='str'),
    forwardfor=dict(default=True, type='bool'),
    addrs = dict(required=True, type='list', elements='dict', options=HAPROXY_FRONTEND_ADDR_ARGUMENT_SPEC)
)

class PFSenseHaproxyFrontendModule(PFSenseModuleBase):
    """ module managing pfsense haproxy Frontends """

    @staticmethod
    def get_argument_spec():
        """ return argument spec """
        return HAPROXY_FRONTEND_ARGUMENT_SPEC

    ##############################
    # init
    #
    def __init__(self, module, pfsense=None):
        super(PFSenseHaproxyFrontendModule, self).__init__(module, pfsense)
        self.name = "pfsense_haproxy_frontend"
        self.obj = dict()

        pkgs_elt = self.pfsense.get_element('installedpackages')
        self.haproxy = pkgs_elt.find('haproxy') if pkgs_elt is not None else None
        self.root_elt = self.haproxy.find('ha_backends') if self.haproxy is not None else None
        if self.root_elt is None:
            self.module.fail_json(msg='Unable to find Frontends XML configuration entry. Are you sure haproxy is installed ?')

    ##############################
    # params processing
    #
    def _addr_params_to_obj(self, addropt):
        ret = dict()

        ret['extaddr'] = 'custom'
        ret['extaddr_custom'] = addropt['addr']
        ret['extaddr_port'] = str(addropt['port'])
        if addropt['ssl']:
            ret['extaddr_ssl'] = 'yes'
        ret['_index'] = ''

        return ret

    def _params_to_obj(self):
        """ return a Frontend dict from module params """
        obj = dict()
        params = self.params

        if self.params['state'] == 'present':
            self._get_ansible_param(obj, 'name')
            self._get_ansible_param(obj, 'descr', fname='desc')
            self._get_ansible_param(obj, 'type')
            self._get_ansible_param(obj, 'httpclose')
            if params["cert_descr"]: 
                obj["ssloffloadcert"] = self.pfsense.find_cert_elt(params["cert_descr"]).find("refid").text
            self._get_ansible_param(obj, 'backend_serverpool')
            self._get_ansible_param_bool(obj, 'forwardfor')
            obj['a_extaddr'] = {
                'item': [self._addr_params_to_obj(x) for x in params['addrs']]
            }
            obj["status"] = "active"
        return obj

    def _validate_params(self):
        """ do some extra checks on input parameters """
        # check name
        if re.search(r'[^a-zA-Z0-9\.\-_]', self.params['name']) is not None:
            self.module.fail_json(msg="The field 'name' contains invalid characters.")
        
        if self.params["cert_descr"] and not self.pfsense.find_cert_elt(self.params["cert_descr"]):
            self.module.fail_json(msg=f'cert_descr, {self.param["cert_descr"]} is not a valid descr of CA')

        for addropt in self.params['addrs']:
            if not self.pfsense.is_ipv4_address(addropt['addr']):
                self.module.fail_json(msg=f'{addropt["addr"]} is not a valid IPv4 address')
    
    ##############################
    # XML processing
    #
    def _create_target(self):
        """ create the XML target_elt """
        server_elt = self.pfsense.new_element('item')
        return server_elt

    def _find_target(self):
        """ find the XML target_elt """
        for item_elt in self.root_elt:
            if item_elt.tag != 'item':
                continue
            name_elt = item_elt.find('name')
            if name_elt is not None and name_elt.text == self.obj['name']:
                return item_elt
        return None

    ##############################
    # run
    #
    def _update(self):
        """ make the target pfsense reload haproxy """
        return self.pfsense.phpshell('''require_once("haproxy/haproxy.inc");
$result = haproxy_check_and_run($savemsg, true); if ($result) unlink_if_exists($d_haproxyconfdirty_path);''')

    ##############################
    # Logging
    #
    def _log_fields(self, before=None):
        """ generate pseudo-CLI command fields parameters to create an obj """
        return ''

    def _get_obj_name(self):
        """ return obj's name """
        return "'{0}'".format(self.obj['name'])

def main():
    module = AnsibleModule(
        argument_spec=HAPROXY_FRONTEND_ARGUMENT_SPEC,
        supports_check_mode=True)

    pfmodule = PFSenseHaproxyFrontendModule(module)
    pfmodule.run(module.params)
    pfmodule.commit_changes()


if __name__ == '__main__':
    main()
