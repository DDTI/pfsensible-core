# -*- coding: utf-8 -*-

# Copyright: (c) 2021, Chris Liu <chris.liu.hk@icloud.com>
# GNU General Public License v3.0+ (see COPYING or https://www.gnu.org/licenses/gpl-3.0.txt)

# TODO: many assumeption: single switch 

from __future__ import absolute_import, division, print_function
import json

__metaclass__ = type
from ansible_collections.pfsensible.core.plugins.module_utils.module_base import PFSenseModuleBase
from ansible.module_utils.basic import AnsibleModule

# <vlangroup>
# 					<vgroup>1</vgroup>
# 					<vlanid>4090</vlanid>
# 					<descr><![CDATA[WAN]]></descr>
# 					<members>9t 10t 1</members>
# 				</vlangroup>
SWITCH_VLAN_ARGUMENT_SPEC = dict(
    state=dict(default='present', choices=['present', 'absent']),

    switch_device=dict(default='/dev/etherswitch0', type='str'),
    vlanid=dict(required=True, type='int'),
    descr=dict(default='', type='str'),
    members=dict(required=True, type='list', elements='str')
)


class PFSenseSwitchVlanModule(PFSenseModuleBase):
    """ module managing pfsense SWITCH_VLANs """

    @staticmethod
    def get_argument_spec():
        """ return argument spec """
        return SWITCH_VLAN_ARGUMENT_SPEC

    ##############################
    # init
    #
    def __init__(self, module, pfsense=None):
        super(PFSenseSwitchVlanModule, self).__init__(module, pfsense)
        self.name = "pfsense_SWITCH_VLAN"

    def _params_to_obj(self):
        """ return a dict from module params """
        params = self.params

        obj = dict()

        if params["state"] == "present":
            self._get_ansible_param(obj, "vlanid")
            self._get_ansible_param(obj, "descr")
            obj["members"] = " ".join(params["members"])

        return obj
    

    def get_switch_vlan_list_and_member_list(self):
        vlan_list = []
        member_list = []
        for vlangroup in self.root_elf.findall("vlangroup"):
            vlanid = vlangroup.find("vlanid").text
            if vlanid  == str(self.params["vlanid"]):
                continue

            vlan_list.append(vlangroup.find("vlanid").text)

            for member in vlangroup.find("members").text.split(" "):
                if member[-1] == 't':
                    # skip tagged port
                    continue
                else:
                    member_list.append(member)
        return vlan_list, member_list

    def _validate_params(self):
        """ do some extra checks on input parameters """
        params = self.params
        self.root_elf = self.pfsense.get_element(f"./switches/switch[device='{params['switch_device']}']/vlangroups")

        if self.root_elf is None:
            self.module.fail_json(msg=f'switch_device, {params["switch_device"]} is unknown switch device')

        vlan_list, member_list = self.get_switch_vlan_list_and_member_list()
        
        # check if vlanid duplicatd
        if params["vlanid"] in vlan_list and params["vlanid"] == 1:
            self.module.fail_json(msg=f'vlan, {params["vlanid"]} is occupied')

        # check members
        for member in params["members"]:
            if member in member_list:
                self.module.fail_json(msg=f'member, {member} is a trunk port and occupied')
        

    ##############################
    # XML processing
    #
    def _find_target(self):
        """ find the XML target_elt """
        for vlangroup in self.root_elf.findall("vlangroup"):
            if vlangroup.find("vlanid").text == str(self.obj["vlanid"]):
                self.obj["vgroup"] = vlangroup.find("vgroup").text
                return vlangroup
        
        ret_elf = self.pfsense.new_element("vlangroup")
        self.obj["vgroup"] = len(self.root_elf)
        self.root_elf.append(ret_elf)
        return ret_elf


    def _get_params_to_remove(self):
        """ returns the list of params to remove if they are not set """
        return []

    @staticmethod
    def convert_members_to_vgmembers(members):
        ret = {}
        for member in members:
            if member[-1] == 't':
                ret[int(member[:-1])] = {'tagged': 1}
            else:
                ret[int(member)] = {}

        return ret
    ##############################
    # run
    #
    def _update(self):
        # convert members from '1 9t 10t' to 
        # {
        #     1:{},
        #     9:{'tagged': 1}
        #     10:{'tagged': 1}
        # }
        
        """ make the target pfsense reload """
        print(f"Chris: {self.obj}")
        return self.pfsense.phpshell(f'''
require_once("switch.inc");
$vgmembers_str_key = json_decode('{json.dumps(self.convert_members_to_vgmembers(self.params["members"]))}',true);
''' + # convert all string key back to integer
''' 
$vgmembers = array();
foreach($vgmembers_str_key as $key => $value){
    $vgmembers[intval($key)] = $value;
}
'''+
f'''
var_dump($vgmembers);
pfSense_etherswitch_setvlangroup('{self.params['switch_device']}', {self.obj["vgroup"]}, {self.obj["vlanid"]}, $vgmembers);
''')

    ##############################
    # Logging
    #
    def _get_obj_name(self):
        """ return obj's name """
        return self.name

    def _log_fields(self, before=None):
        """ generate pseudo-CLI command fields parameters to create an obj """
        values = ''
        # todo: hosts and domainoverrides is not logged
        return values



def main():
    module = AnsibleModule(
        argument_spec=SWITCH_VLAN_ARGUMENT_SPEC,
        required_if=[],
        supports_check_mode=True)

    pfmodule = PFSenseSwitchVlanModule(module)
    pfmodule.run(module.params)
    pfmodule.commit_changes()


if __name__ == '__main__':
    main()