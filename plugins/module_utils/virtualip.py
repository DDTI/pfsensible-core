# -*- coding: utf-8 -*-

# Copyright: (c) 2018, Frederic Bor <frederic.bor@wanadoo.fr>
# GNU General Public License v3.0+ (see COPYING or https://www.gnu.org/licenses/gpl-3.0.txt)

from __future__ import absolute_import, division, print_function
__metaclass__ = type
import re
from ansible_collections.pfsensible.core.plugins.module_utils.module_base import PFSenseModuleBase

virtualip_ARGUMENT_SPEC = dict(
    state=dict(default='present', choices=['present', 'absent']),
    descr=dict(required=True, type='str'),
    mode=dict(required=False, choices=['ipalias','proxyarp','carp','other']),
    interface_descr=dict(required=False, type='str'),
    vhid=dict(required=False, type='int', default=1),
    advskew=dict(default=0, required=False, type='int'),
    advbase=dict(default=1, type='int'),
    password=dict(type='str'),
    ipv4_address=dict(type='str'),
    ipv4_prefixlen=dict(default=32, type='int')
)

virtualip_REQUIRED_IF = [
    ["state", "present", ["mode", "ipv4_address"]],
]

virtualip_MUTUALLY_EXCLUSIVE=[]

class PFSenseVirtualipModule(PFSenseModuleBase):
    """ module managing pfsense virtualips """

    @staticmethod
    def get_argument_spec():
        """ return argument spec """
        return virtualip_ARGUMENT_SPEC

    ##############################
    # init
    #
    def __init__(self, module, pfsense=None):
        super(PFSenseVirtualipModule, self).__init__(module, pfsense)
        self.name = "pfsense_virtualip"
        self.obj = dict()

        self.root_elt = self.pfsense.virtualip
        if self.root_elt is None:
            self.root_elt = self.pfsense.new_element("virtualip")
            self.pfsense.root.append(self.root_elt)
        self.target_idx = None
        self.is_delete = False

    ##############################
    # params processing
    #
    def _params_to_obj(self):
        """ return an virtualip dict from module params """
        params = self.params

        obj = dict()
        self.obj = obj
        
        obj['descr'] = params['descr']
        if params['state'] == 'present':
            self._get_ansible_param(obj, 'vhid')
            self._get_ansible_param(obj, 'advskew')
            self._get_ansible_param(obj, 'advbase')
            self._get_ansible_param(obj, 'password')
            self._get_ansible_param(obj, 'ipv4_address', fname='subnet')
            self._get_ansible_param(obj, 'ipv4_prefixlen', fname='subnet_bits')
            self._get_ansible_param(obj, 'mode')

            obj["uniqid"] = self.pfsense.uniqid()

            if obj["subnet_bits"] == 32:
                obj["type"] = "single"
            else:
                obj["type"] = "network"

            obj["interface"] = self.pfsense.get_interface_by_display_name(params["interface_descr"])
        else:
            self.is_delete = True

        self.target_idx, self.target_elt = self._get_idx_virtualip_elt_by_display_name(self.obj['descr'])
        
        return obj

    def _validate_params(self):
        """ do some extra checks on input parameters """

        params = self.params

        # check name
        if re.match('^[a-zA-Z0-9_]+$', params['descr']) is None:
            self.module.fail_json(msg='The name of the virtualip may only consist of the characters "a-z, A-Z, 0-9 and _"')

        if params['state'] == 'present':
            if params.get('ipv4_prefixlen') is not None and params['ipv4_prefixlen'] < 1 or params['ipv4_prefixlen'] > 32:
                self.module.fail_json(msg='ipv4_prefixlen must be between 1 and 32.')

            if params.get('ipv4_address') and not self.pfsense.is_ipv4_address(params['ipv4_address']):
                self.module.fail_json(msg='{0} is not a valid IPv4 address'.format(params['ipv4_address']))
        
        if not self.pfsense.is_interface_display_name(params['interface_descr']):
            self.module.fail_json(msg='{0} is not a valid interface display name'.format(params['interface_descr']))

    ##############################
    # XML processing
    #
    def _copy_and_add_target(self):
        """ create the XML target_elt """
        self.pfsense.copy_dict_to_element(self.obj, self.target_elt)

    def _copy_and_update_target(self):
        """ update the XML target_elt """
        before = self.pfsense.element_to_dict(self.target_elt)
        changed = self.pfsense.copy_dict_to_element(self.obj, self.target_elt)
        if self._remove_deleted_params():
            changed = True

        return (before, changed)

    def _create_target(self):
        """ create the XML target_elt """
        virtualip_elt = self.pfsense.new_element('vip')
        self.target_idx = self._get_virtualip_last_idx()
        self.root_elt.insert(self.target_idx, virtualip_elt)

        return virtualip_elt

    def _get_virtualip_last_idx(self):
        return len(self.root_elt)

    def _get_virtualip_elt_by_display_name(self, name):
        return self._get_idx_virtualip_elt_by_display_name(name)[1]
    
    def _get_idx_virtualip_elt_by_display_name(self, name):
        """ return pfsense virtualip by name """
        assert(self.root_elt is not None)
        for idx, iface in enumerate(self.root_elt):
            descr_elt = iface.find('descr')
            if descr_elt is None:
                continue
            if descr_elt.text is None:
                continue
            if descr_elt.text.strip().lower() == name.lower():
                return (idx, iface)
        return (None, None)

    def _find_target(self):
        """ find the XML target_elt """
        return self.target_elt

    @staticmethod
    def _get_params_to_remove():
        """ returns the list of params to remove if they are not set """
        return []

    ##############################
    # run
    #

    def _update(self):
        
        if self.target_idx is None:
            self.module.fail_json(msg=f'the target idx is None for if: {self.obj["descr"]}')

        if self.is_delete:
            return self.pfsense.phpshell(f"""
require_once("firewall_virtual_ip.inc");
deleteVIP({self.target_idx});
""")
        else:
            """ make the target pfsense reload virtualips , copy from https://github.com/pfsense/pfsense/blob/1004053d3ae9c350e20249d65783b6c4a63b0e58/src/usr/local/pfSense/include/www/firewall_virtual_ip.inc"""
            return self.pfsense.phpshell("""
require_once("config.gui.inc");
require_once("util.inc");
require_once("interfaces.inc");
require_once("filter.inc");
require_once("pfsense-utils.inc");
global $config, $g;
$a_vip = &$config['virtualip']['vip'];
""" + f"$vid = {self.target_idx};"+ """
$check_carp = false;
switch ($a_vip[$vid]['mode']) {
case "ipalias":
    interface_ipalias_configure($a_vip[$vid]);
    break;
case "proxyarp":
    interface_proxyarp_configure($a_vip[$vid]['interface']);

    break;
case "carp":
    $check_carp = true;
    interface_carp_configure($a_vip[$vid]);
    break;
default:
    break;
}
if ($a_vip[$vid]['mode'] != 'proxyarp') {
    foreach ($a_vip as $avip) { 
        if (($avip['interface'] == $a_vip[$vid]['interface']) &&
            ($avip['mode'] == 'proxyarp')) {
            interface_proxyarp_configure($a_vip[$vid]['interface']);
            break;
        }
    }
}
if ($check_carp === true && !get_carp_status()) {
    set_single_sysctl("net.inet.carp.allow", "1");
}
filter_configure();
clear_subsystem_dirty('vip');
    """)

    ##############################
    # Logging
    #
    def _get_obj_name(self):
        """ return obj's name """
        return "'{0}'".format(self.obj['descr'])

    def _log_fields(self, before=None):
        """ generate pseudo-CLI command fields parameters to create an obj """
        values = ''
        if before is None:
            values += self.format_cli_field(self.obj, 'descr')
            values += self.format_cli_field(self.obj, 'interface')
            values += self.format_cli_field(self.obj, 'vhid')
            values += self.format_cli_field(self.obj, 'advskew')
            values += self.format_cli_field(self.obj, 'advbase')
            values += self.format_cli_field(self.obj, 'password')
            values += self.format_cli_field(self.obj, 'ipv4_address')
            values += self.format_cli_field(self.obj, 'ipv4_prefixlen')
            values += self.format_cli_field(self.obj, 'uniqid')
            values += self.format_cli_field(self.obj, 'type')
            values += self.format_cli_field(self.obj, 'mode')
        else:
            # todo: - detect before ipv4_type for proper logging
            values += self.format_updated_cli_field(self.obj, before, 'descr', add_comma=(values))
            values += self.format_updated_cli_field(self.obj, before, 'interface', add_comma=(values))
            values += self.format_updated_cli_field(self.obj, before, 'vhid', add_comma=(values))
            values += self.format_updated_cli_field(self.obj, before, 'advskew', add_comma=(values))
            values += self.format_updated_cli_field(self.obj, before, 'advbase', add_comma=(values))
            values += self.format_updated_cli_field(self.obj, before, 'password', add_comma=(values))
            values += self.format_updated_cli_field(self.obj, before, 'ipv4_address', add_comma=(values))
            values += self.format_updated_cli_field(self.obj, before, 'ipv4_prefixlen', add_comma=(values))
            values += self.format_updated_cli_field(self.obj, before, 'type', add_comma=(values))
            values += self.format_updated_cli_field(self.obj, before, 'mode', add_comma=(values))
        return values
