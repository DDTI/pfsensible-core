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

SUDO_ARGUMENT_SPEC = dict(
    state=dict(default='present', choices=['present', 'absent']),
    username=dict(required=True, type='str'),
    runas=dict(required=True, type='str'),
    cmdlist=dict(required=True, type='str'),
    nopasswd=dict(required=True, type='bool'),
)

class PFSenseSudoModule(PFSenseModuleBase):
    """ module managing pfsense haproxy Frontends """

    @staticmethod
    def get_argument_spec():
        """ return argument spec """
        return SUDO_ARGUMENT_SPEC

    ##############################
    # init
    #
    def __init__(self, module, pfsense=None):
        super(PFSenseSudoModule, self).__init__(module, pfsense)
        self.name = "pfsense_sudo"
        self.obj = dict()

        pkgs_elt = self.pfsense.get_element('installedpackages')
        self.haproxy = pkgs_elt.find('sudo') if pkgs_elt is not None else None
        self.root_elt = self.haproxy.find('config') if self.haproxy is not None else None
        if self.root_elt is None:
            self.module.fail_json(msg='Unable to find sudo XML configuration entry. Are you sure sudo is installed ?')

    ##############################
    # params processing
    #
    def _params_to_obj(self):
        """ return a Frontend dict from module params """
        obj = dict()
        params = self.params

        if self.params['state'] == 'present':
            for option in ['username', 'runas', 'cmdlist', '']:
                if option in params and params[option] is not None:
                    obj[option] = params[option]
            if params["nopasswd"]:
                obj['nopasswd'] = "ON"
        return obj

    def is_user_group(self, s):
        if s.startswith('user:') or s.startswith('group:'):
            return True
        else:
            return False
            
    def _validate_params(self):
        """ do some extra checks on input parameters """
        if not self.is_user_group(self.params['username']):
            self.module.fail_json(msg='`username` is not start with `user:` or `group:`')
        if not self.is_user_group(self.params['runas']):
            self.module.fail_json(msg='`runas` is not start with `user:` or `group:`')
    
    def _get_params_to_remove(self):
        """ returns the list of params to remove if they are not set """
        return ["nopasswd"]
    ##############################
    # XML processing
    #
    def _create_target(self):
        """ create the XML target_elt """
        server_elt = self.pfsense.new_element('row')
        return server_elt

    def _find_target(self):
        """ find the XML target_elt """
        for item_elt in self.root_elt:
            if item_elt.tag != 'row':
                continue
            name_elt = item_elt.find('username')
            if name_elt is not None and name_elt.text == self.obj['username']:
                return item_elt
        return None

    ##############################
    # run
    #
    def _update(self):
        """ make the target pfsense reload haproxy """
        return self.pfsense.phpshell('''require_once("sudo/sudo.inc"); sudo_write_config();''')

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
        argument_spec=SUDO_ARGUMENT_SPEC,
        supports_check_mode=True)

    pfmodule = PFSenseSudoModule(module)
    pfmodule.run(module.params)
    pfmodule.commit_changes()


if __name__ == '__main__':
    main()
