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

LAGG_ARGUMENT_SPEC = dict(
    state=dict(default='present', choices=['present', 'absent']),

    members=dict(requried=True, type='list', elements='str'),
    descr=dict(requried=True, type='str'),
    proto=dict(requried=True, choices=["none", "lacp", "failover", "loadbalance", "roundrobin"]),
    lacptimeout=dict(default='slow', choices=['slow', 'fast']),
    laggif=dict(required=True, type='str'),
)

class PFSenselaggModule(PFSenseModuleBase):
    """ module managing pfsense laggs """

    @staticmethod
    def get_argument_spec():
        """ return argument spec """
        return LAGG_ARGUMENT_SPEC

    ##############################
    # init
    #
    def __init__(self, module, pfsense=None):
        super(PFSenselaggModule, self).__init__(module, pfsense)
        self.name = "pfsense_lagg"

        self.id = None
        
    def _params_to_obj(self):
        """ return a dict from module params """
        params = self.params

        obj = dict()

        if params["state"] == "present":
            obj["members"] = ",".join(params["members"])
            self._get_ansible_param(obj,'descr')
            self._get_ansible_param(obj,'proto')
            self._get_ansible_param(obj,'laggif')
        return obj

    def _validate_params(self):
        """ do some extra checks on input parameters """
        params = self.params
        ports = self.pfsense.get_ports()

        for member in params["members"]:
            if not member in ports:
                self.module.fail_json(msg=f'member, {member} is not a valid port')

    ##############################
    # XML processing
    #

    def _find_target(self):
        """ find the XML target_elt """
        obj = self.obj
        
        lagg_elt = self.pfsense.get_element("laggs", create_node=True)
        
        target_elt=None
        for idx, elt in enumerate(lagg_elt.findall("lagg")):
            if self.params["laggif"] == elt.find("laggif").text:
                target_elt = elt
                self.id = idx
        
        if self.id is None:
            self.id = len(lagg_elt.findall("lagg"))
        
        if not target_elt:
            target_elt = self.pfsense.new_element("lagg")
            lagg_elt.append(target_elt)

        return target_elt

    def _get_params_to_remove(self):
        """ returns the list of params to remove if they are not set """
        return []

    ##############################
    # run
    #
    def commit_changes(self):
        """ make the target pfsense reload, copy from https://github.com/pfsense/pfsense/blob/master/src/usr/local/www/interfaces_lagg_edit.php"""
        
        (dummy, self.result['stdout'], self.result['stderr']) = self.pfsense.phpshell(f'''
require_once("config.lib.inc");
require_once("interfaces.inc");

init_config_arr(array('laggs', 'lagg'));
$a_laggs = &$config['laggs']['lagg'];
$lagg = json_decode('{json.dumps(self.obj)}', true);
$id = {self.id};
'''+
'''
$lagg['laggif'] = interface_lagg_configure($lagg);
$a_laggs[$id] = $lagg;

write_config("LAGG interface added");

$confif = convert_real_interface_to_friendly_interface_name($lagg['laggif']);
if ($confif != "") {
    interface_configure($confif);
}

// reconfigure any VLANs with this lagg as their parent
if (is_array($config['vlans']['vlan'])) {
    foreach ($config['vlans']['vlan'] as $vlan) {
        if ($vlan['if'] == $lagg['laggif']) {
            interface_vlan_configure($vlan);
            $confif = convert_real_interface_to_friendly_interface_name($vlan['vlanif']);
            if ($confif != "") {
                interface_configure($confif);
            }
        }
    }
}
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
        argument_spec=LAGG_ARGUMENT_SPEC,
        required_if=[],
        supports_check_mode=True)

    pfmodule = PFSenselaggModule(module)
    pfmodule.run(module.params)
    pfmodule.commit_changes()


if __name__ == '__main__':
    main()
