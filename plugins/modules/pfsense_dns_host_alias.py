# -*- coding: utf-8 -*-

# Copyright: (c) 2021, Chris Liu <chris.liu.hk@icloud.com>
# GNU General Public License v3.0+ (see COPYING or https://www.gnu.org/licenses/gpl-3.0.txt)

from __future__ import absolute_import, division, print_function
import base64
import copy
__metaclass__ = type
from ansible_collections.pfsensible.core.plugins.module_utils.module_base import PFSenseModuleBase
from ansible.module_utils.basic import AnsibleModule

DNS_ARGUMENT_SPEC = dict(
    state=dict(default='present', choices=['present', 'absent']),
    host=dict(required=True, type='str'),
    domain=dict(required=True, type='str'),
    ip=dict(required=True, type='str'),
    descr=dict(default="", type='str'),
)

dns_REQUIRED_IF = []


class PFSenseDNSModule(PFSenseModuleBase):
    """ module managing pfsense dnss """

    @staticmethod
    def get_argument_spec():
        """ return argument spec """
        return DNS_ARGUMENT_SPEC

    ##############################
    # init
    #
    def __init__(self, module, pfsense=None):
        super(PFSenseDNSModule, self).__init__(module, pfsense)
        self.name = "pfsense_dns_host_alias"
        self.root_elt = self.pfsense.get_element('unbound')
        self.hosts = self.root_elt.findall('hosts')

    def _params_to_obj(self):
        """ return a dict from module params """
        params = self.params

        obj = dict()
        self.obj = obj

        obj['host'] = params['host']
        obj['domain'] = params['domain']
        if params['state'] == 'present':
            obj['ip'] = params['ip']
            if params['descr'] is not None:
                obj['descr'] = params['descr']

        return obj

    def _validate_params(self):
        """ do some extra checks on input parameters """
        params = self.params

        if not self.pfsense.is_ipv4_address(params["ip"]):
            self.module.fail_json(msg=f'ip, {params["ip"]} is not a ipv4 address')


    ##############################
    # XML processing
    #
    def _copy_and_add_target(self):
        """ create the XML target_elt """

        # if self._find_by_host_and_domain(self.obj['host'], self.obj['domain']) is not None:
        #     self.module.fail_json(msg='A different host alias already exists with host {0} and domain {1}.'.format(self.obj['host'], self.obj['domain']))

        self.pfsense.copy_dict_to_element(self.obj, self.target_elt)
        self.diff['after'] = self.pfsense.element_to_dict(self.target_elt)
        self.root_elt.insert(self._find_last_index(), self.target_elt)
        # Reset hosts list
        self.hosts = self.root_elt.findall('hosts')

    def _copy_and_update_target(self):
        before = self.pfsense.element_to_dict(self.target_elt)
        self.diff['before'] = before
        changed = self.pfsense.copy_dict_to_element(self.obj, self.target_elt)
        self.diff['after'].update(self.pfsense.element_to_dict(self.target_elt))

        return (before, changed)

    def _find_this_index(self):
        return self.hosts.index(self.target_elt)

    def _find_last_index(self):
        if len(self.hosts) < 1:
            return 0

        return list(self.root_elt).index(self.hosts[len(self.hosts) - 1])

    def _create_target(self):
        return self.pfsense.new_element('hosts')

    def _find_target(self):
        host = self.obj["host"]
        domain = self.obj["domain"]

        for host_elt in self.root_elt.findall(f"hosts[host='{host}']"):
            if host_elt.find('domain').text == domain:
                return host_elt

        return None

    ##############################
    # run
    #
    def _update(self):
        """ make the target pfsense reload """
        return self.pfsense.phpshell('''
require_once("unbound.inc");
require_once("pfsense-utils.inc");
require_once("system.inc");

services_unbound_configure();
system_resolvconf_generate();
system_dhcpleases_configure();
clear_subsystem_dirty("unbound");
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

        # values += self.format_updated_cli_field(self.obj, before, 'host', fvalue=self.fvalue_bool, add_comma=(values), log_none=False)
        # values += self.format_updated_cli_field(self.obj, before, 'domain', fvalue=self.fvalue_bool, add_comma=(values), log_none=False)
        # values += self.format_updated_cli_field(self.obj, before, 'ip', fvalue=self.fvalue_bool, add_comma=(values), log_none=False)
        # values += self.format_updated_cli_field(self.obj, before, 'descr', fvalue=self.fvalue_bool, add_comma=(values), log_none=False)

        # todo: hosts and domainoverrides is not logged
        return values



def main():
    module = AnsibleModule(
        argument_spec=DNS_ARGUMENT_SPEC,
        required_if=dns_REQUIRED_IF,
        supports_check_mode=True)

    pfmodule = PFSenseDNSModule(module)
    pfmodule.run(module.params)
    pfmodule.commit_changes()


if __name__ == '__main__':
    main()
