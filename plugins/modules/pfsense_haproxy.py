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

HAPROXY_ARGUMENT_SPEC = dict(
    state=dict(default='present', choices=['present', 'absent']),
    maxconn=dict(default=1000, type='int'),
    localstatsport=dict(default=2200, type='int'),
    ssldefaultdhparam=dict(default=2048, type='int'),
    enablesync=dict(defaut=None, type='bool'),
    carpdev=dict(defaut=None, type='str')
)

class PFSenseHaproxyModule(PFSenseModuleBase):
    """ module managing pfsense haproxy Frontends """

    @staticmethod
    def get_argument_spec():
        """ return argument spec """
        return HAPROXY_ARGUMENT_SPEC

    ##############################
    # init
    #
    def __init__(self, module, pfsense=None):
        super(PFSenseHaproxyModule, self).__init__(module, pfsense)
        self.name = "pfsense_HAPROXY"
        self.obj = dict()

        pkgs_elt = self.pfsense.get_element('installedpackages')
        self.root_elt = pkgs_elt.find('haproxy') if pkgs_elt is not None else None
        if self.root_elt is None:
            self.module.fail_json(msg='Unable to find Frontends XML configuration entry. Are you sure haproxy is installed ?')

    ##############################
    # params processing
    #
    def _params_to_obj(self):
        """ return a Frontend dict from module params """
        obj = dict()
        params = self.params

        if self.params['state'] == 'present':
            self._get_ansible_param(obj, 'maxconn')
            self._get_ansible_param(obj, 'localstatsport')
            self._get_ansible_param(obj, 'ssldefaultdhparam')
            self._get_ansible_param_bool(obj, 'enablesync')
            self._get_ansible_param(obj, 'carpdev')

        return obj

    def _validate_params(self):
        """ do some extra checks on input parameters """
        if not self.pfsense.is_ipv4_address(self.params["carpdev"]):
            self.module.fail_json(msg=f'{self.params["carpdev"]} is not a valid IPv4 address')
    
    def _get_params_to_remove(self):
        return ['carpdev', 'enablesync']

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
        return self.name

def main():
    module = AnsibleModule(
        argument_spec=HAPROXY_ARGUMENT_SPEC,
        supports_check_mode=True)

    pfmodule = PFSenseHaproxyModule(module)
    pfmodule.run(module.params)
    pfmodule.commit_changes()


if __name__ == '__main__':
    main()
