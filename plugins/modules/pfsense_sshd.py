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



SSHD_ARGUMENT_SPEC = dict(
    state=dict(default='present', choices=['present', 'absent']),
    sshdkeyonly=dict(default=None, choices=['enabled', 'both', None])
)

class PFSenseSshdModule(PFSenseModuleBase):
    """ module managing pfsense haproxy Frontends """

    @staticmethod
    def get_argument_spec():
        """ return argument spec """
        return SSHD_ARGUMENT_SPEC

    ##############################
    # init
    #
    def __init__(self, module, pfsense=None):
        super(PFSenseSshdModule, self).__init__(module, pfsense)
        self.name = "pfsense_sshd"
        self.obj = dict()

        system_elt = self.pfsense.get_element('system')
        self.root_elt = system_elt.find('ssh')
        if self.root_elt is None:
            self.module.fail_json(msg='Unable to find ssh element in system. ')

    ##############################
    # params processing
    #

    def _params_to_obj(self):
        """ return a Frontend dict from module params """
        obj = dict()

        # force enable here. Otherwise ansible wont work    
        obj['enable'] = 'enabled'
        obj['sshdkeyonly'] = self.params['sshdkeyonly']

        return obj

    def _validate_params(self):
        """ do some extra checks on input parameters """
            
    ##############################
    # XML processing
    #
    def _find_target(self):
        """ find the XML target_elt """
        return self.root_elt

    ##############################
    # run
    #
    def _update(self):
        """ make the target pfsense reload haproxy """
        return self.pfsense.phpshell('''
        require_once("util.inc");

        killbyname("sshd");
        send_event("service restart sshd");
        ''')

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
        argument_spec=SSHD_ARGUMENT_SPEC,
        supports_check_mode=True)

    pfmodule = PFSenseSshdModule(module)
    pfmodule.run(module.params)
    pfmodule.commit_changes()


if __name__ == '__main__':
    main()
