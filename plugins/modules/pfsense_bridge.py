# -*- coding: utf-8 -*-

# Copyright: (c) 2021, Chris Liu <chris.liu.hk@icloud.com>
# GNU General Public License v3.0+ (see COPYING or https://www.gnu.org/licenses/gpl-3.0.txt)

from __future__ import absolute_import, division, print_function
import base64
import os
import json

__metaclass__ = type
from ansible_collections.pfsensible.core.plugins.module_utils.module_base import PFSenseModuleBase
from ansible.module_utils.basic import AnsibleModule

BRIDGE_ARGUMENT_SPEC = dict(
    state=dict(default='present', choices=['present', 'absent']),

    members=dict(requried=True, type='list', elements='str'),
    descr=dict(requried=True, type='str'),
    bridgeif=dict(required=True, type='str')
)

class PFSenseBridgeModule(PFSenseModuleBase):
    """ module managing pfsense bridges """

    @staticmethod
    def get_argument_spec():
        """ return argument spec """
        return BRIDGE_ARGUMENT_SPEC

    ##############################
    # init
    #
    def __init__(self, module, pfsense=None):
        super(PFSenseBridgeModule, self).__init__(module, pfsense)
        self.name = "pfsense_bridge"
        self.root_elt = self.pfsense.get_element("bridges")
        if self.root_elt is None:
            self.root_elt = self.pfsense.new_element("bridges")
            self.pfsense.root.append(self.root_elt)
        
    def _params_to_obj(self):
        """ return a dict from module params """
        params = self.params

        obj = dict()

        if params["state"] == "present":
            obj["members"] = ",".join(map(self.pfsense.get_interface_by_display_name, params["members"]))
            self._get_ansible_param(obj,'descr')
            self._get_ansible_param(obj,'bridgeif')
        return obj

    def _validate_params(self):
        """ do some extra checks on input parameters """
        params = self.params

        for member in params["members"]:
            if not self.pfsense.is_interface_display_name(member):
                self.module.fail_json(msg=f'member, {member} is not a valid descr of interface')

    ##############################
    # XML processing
    #

    def _find_target(self):
        """ find the XML target_elt """
        obj = self.obj

        for elt in self.root_elt.findall("bridged"):
            if elt.find("bridgeif").text == self.params["bridgeif"]:
                return elt

        return None

    def _create_target(self):
        return self.pfsense.new_element("bridged")

    def _get_params_to_remove(self):
        """ returns the list of params to remove if they are not set """
        return []

    ##############################
    # run
    #
    def _update(self):
        """ make the target pfsense reload, copy from https://github.com/pfsense/pfsense/blob/master/src/usr/local/www/interfaces_bridge_edit.php"""
        if self.params["state"] == 'present':
            (dummy, self.result['stdout'], self.result['stderr']) = self.pfsense.phpshell(f'''
    require_once("interfaces.inc");

    $bridge = json_decode('{json.dumps(self.obj)}', true);
    interface_bridge_configure($bridge);
    ''')
            self.module.exit_json(**self.result)
        else:
            (dummy, self.result['stdout'], self.result['stderr']) = self.pfsense.phpshell(f'''
    require_once("interfaces.inc");
    pfSense_interface_destroy('{self.params["bridgeif"]}');
    ''')
            self.module.exit_json(**self.result)
            

    ##############################
    # Logging
    #
    def _get_obj_name(self):
        """ return obj's name """
        return self.name

    def _log_fields(self, before=None):
        """ generate pseudo-CLI command fields parameters to create an obj """
        return ''



def main():
    module = AnsibleModule(
        argument_spec=BRIDGE_ARGUMENT_SPEC,
        required_if=[],
        supports_check_mode=True)

    pfmodule = PFSenseBridgeModule(module)
    pfmodule.run(module.params)
    pfmodule.commit_changes()


if __name__ == '__main__':
    main()
