#!/usr/bin/python
# -*- coding: utf-8 -*-

# Copyright: (c) 2019, Frederic Bor <frederic.bor@wanadoo.fr>
# GNU General Public License v3.0+ (see COPYING or https://www.gnu.org/licenses/gpl-3.0.txt)

from __future__ import absolute_import, division, print_function
import base64
import re
from ansible.module_utils.basic import AnsibleModule
from ansible_collections.pfsensible.core.plugins.module_utils.module_base import PFSenseModuleBase

__metaclass__ = type

ANSIBLE_METADATA = {'metadata_version': '1.1',
                    'status': ['preview'],
                    'supported_by': 'community'}

OPENVPN_EXPORT_ARGUMENT_SPEC = dict(
    state=dict(default='present', choices=['present', 'absent']),
    advancedoptions=dict(default='', type='str'),
    openvpn_server_descr = dict(required=True, type='str')
)

class PFSenseOpenVPNExportModule(PFSenseModuleBase):
    """ module managing pfsense haproxy Frontends """

    @staticmethod
    def get_argument_spec():
        """ return argument spec """
        return OPENVPN_EXPORT_ARGUMENT_SPEC

    ##############################
    # init
    #
    def __init__(self, module, pfsense=None):
        super(PFSenseOpenVPNExportModule, self).__init__(module, pfsense)
        self.name = "pfsense_OPENVPN_EXPORT"
        self.obj = dict()

        pkgs_elt = self.pfsense.get_element('installedpackages')
        vpn_openvpn_export_elt = pkgs_elt.find('vpn_openvpn_export') if pkgs_elt is not None else None
        self.root_elt = vpn_openvpn_export_elt.find('serverconfig') if pkgs_elt is not None else None
        if self.root_elt is None:
            self.module.fail_json(msg='Unable to find vpn_openvpn_export XML configuration entry. Are you sure vpn_openvpn_export is installed ?')

    ##############################
    # params processing
    #
    
    def get_server_id_by_server_desc(self, openvpn_server_descr):
        for idx, elt in enumerate(self.pfsense.get_element('openvpn').findall('openvpn-server')):
            if elt.find('description').text == openvpn_server_descr:
                # self.module.fail_json(msg=f"Debug idx:{idx} {elt.find('description').text}")
                return idx + 1
        return None

    def _params_to_obj(self):
        """ return a Frontend dict from module params """
        obj = dict()
        params = self.params

        if self.params['state'] == 'present':
            obj['advancedoptions'] = base64.b64encode(params['advancedoptions'].encode()).decode()
            obj['server'] = self.get_server_id_by_server_desc(params['openvpn_server_descr'])
            if obj['server'] is None:
                self.module.fail_json(msg=f'Unknown openvpn_server_descr: {params["openvpn_server_descr"]}')

        return obj

    def _validate_params(self):
        """ do some extra checks on input parameters """
        pass
            
    ##############################
    # XML processing
    #

    def _create_target(self):
        """ create the XML target_elt """
        ret_elt = self.pfsense.new_element('item')
        self.root_elt.append(ret_elt)
        return ret_elt

    def _find_target(self):
        """ find the XML target_elt """
        for item in self.root_elt.findall('item'):
            if int(item.find("server").text) == self.obj['server']:
                return item

        return None


    ##############################
    # run
    #

    ##############################
    # Logging
    #
    def _log_fields(self, before=None):
        """ generate pseudo-CLI command fields parameters to create an obj """
        return ''

    def _get_obj_name(self):
        """ return obj's name """
        return self.name

def main():
    module = AnsibleModule(
        argument_spec=OPENVPN_EXPORT_ARGUMENT_SPEC,
        supports_check_mode=True)

    pfmodule = PFSenseOpenVPNExportModule(module)
    pfmodule.run(module.params)
    pfmodule.commit_changes()


if __name__ == '__main__':
    main()
