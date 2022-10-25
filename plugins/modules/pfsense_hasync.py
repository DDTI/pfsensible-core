# -*- coding: utf-8 -*-

# Copyright: (c) 2021, Chris Liu <chris.liu.hk@icloud.com>
# GNU General Public License v3.0+ (see COPYING or https://www.gnu.org/licenses/gpl-3.0.txt)

from __future__ import absolute_import, division, print_function
__metaclass__ = type
from ansible_collections.pfsensible.core.plugins.module_utils.module_base import PFSenseModuleBase
from ansible.module_utils.basic import AnsibleModule

HASYNC_ARGUMENT_SPEC = dict(
    state=dict(default='present', choices=['present', 'absent']),

    pfsyncenabled=dict(default=False, type='bool'),
    adminsync=dict(default=False, type='bool'),
    synchronizeusers=dict(default=False, type='bool'),
    synchronizeauthservers=dict(default=False, type='bool'),
    synchronizecerts=dict(default=False, type='bool'),
    synchronizerules=dict(default=False, type='bool'),
    synchronizeschedules=dict(default=False, type='bool'),
    synchronizealiases=dict(default=False, type='bool'),
    synchronizenat=dict(default=False, type='bool'),
    synchronizeipsec=dict(default=False, type='bool'),
    synchronizeopenvpn=dict(default=False, type='bool'),
    synchronizedhcpd=dict(default=False, type='bool'),
    synchronizedhcrelay=dict(default=False, type='bool'),
    synchronizedhcrelay6=dict(default=False, type='bool'),
    synchronizewol=dict(default=False, type='bool'),
    synchronizestaticroutes=dict(default=False, type='bool'),
    synchronizevirtualip=dict(default=False, type='bool'),
    synchronizetrafficshaper=dict(default=False, type='bool'),
    synchronizetrafficshaperlimiter=dict(default=False, type='bool'),
    synchronizednsforwarder=dict(default=False, type='bool'),
    synchronizecaptiveportal=dict(default=False, type='bool'),
    pfsyncpeerip=dict(default=None, type='str'),
    pfsyncinterface=dict(default=None, type='str'),
    synchronizetoip=dict(default=None, type='str'),
    username=dict(default=None, type='str'),
    password=dict(default=None, type='str'),
)

hasync_REQUIRED_IF = []


class PFSenseHasyncModule(PFSenseModuleBase):
    """ module managing pfsense hasyncs """

    @staticmethod
    def get_argument_spec():
        """ return argument spec """
        return HASYNC_ARGUMENT_SPEC

    ##############################
    # init
    #
    def __init__(self, module, pfsense=None):
        super(PFSenseHasyncModule, self).__init__(module, pfsense)
        self.name = "pfsense_hasync"
        self.root_elt = self.pfsense.get_element('hasync')
        self.obj = dict()
        self.interface_elt = None
        self.dynamic = False

        if self.root_elt is None:
            self.root_elt = self.pfsense.new_element('hasync')
            self.pfsense.root.append(self.root_elt)

    ##############################
    # params processing
    #
    def _params_to_obj(self):
        """ return a dict from module params """
        params = self.params

        obj = dict()

        if params["state"] == "present":
            self._get_ansible_param_bool(obj, 'pfsyncenabled', value="on")
            self._get_ansible_param_bool(obj, 'adminsync', value="on")
            self._get_ansible_param_bool(obj, 'synchronizeusers', value="on")
            self._get_ansible_param_bool(obj, 'synchronizeauthservers', value="on")
            self._get_ansible_param_bool(obj, 'synchronizecerts', value="on")
            self._get_ansible_param_bool(obj, 'synchronizerules', value="on")
            self._get_ansible_param_bool(obj, 'synchronizeschedules', value="on")
            self._get_ansible_param_bool(obj, 'synchronizealiases', value="on")
            self._get_ansible_param_bool(obj, 'synchronizenat', value="on")
            self._get_ansible_param_bool(obj, 'synchronizeipsec', value="on")
            self._get_ansible_param_bool(obj, 'synchronizeopenvpn', value="on")
            self._get_ansible_param_bool(obj, 'synchronizedhcpd', value="on")
            self._get_ansible_param_bool(obj, 'synchronizedhcrelay', value="on")
            self._get_ansible_param_bool(obj, 'synchronizedhcrelay6', value="on")
            self._get_ansible_param_bool(obj, 'synchronizewol', value="on")
            self._get_ansible_param_bool(obj, 'synchronizestaticroutes', value="on")
            self._get_ansible_param_bool(obj, 'synchronizevirtualip', value="on")
            self._get_ansible_param_bool(obj, 'synchronizetrafficshaper', value="on")
            self._get_ansible_param_bool(obj, 'synchronizetrafficshaperlimiter', value="on")
            self._get_ansible_param_bool(obj, 'synchronizednsforwarder', value="on")
            self._get_ansible_param_bool(obj, 'synchronizecaptiveportal', value="on")
        
            self._get_ansible_param(obj, 'pfsyncpeerip')
            obj['pfsyncinterface'] = self.pfsense.get_interface_by_display_name(params['pfsyncinterface'])
            self._get_ansible_param(obj, 'synchronizetoip')
            self._get_ansible_param(obj, 'username')
            self._get_ansible_param(obj, 'password')
            # if params['username'] is not None:
            #     obj['username'] = f'<![CDATA[{params["username"]}]]>'
            # if params['password'] is not None:
            #     obj['password'] = f'<![CDATA[{params["password"]}]]>'
        
        return obj

    def _validate_params(self):
        """ do some extra checks on input parameters """
        params = self.params

        if params["pfsyncpeerip"] is not None and not self.pfsense.is_ipv4_address(params["pfsyncpeerip"]):
            self.module.fail_json(msg='pfsyncpeerip is not a valid ip address')
        if params["synchronizetoip"] is not None and not self.pfsense.is_ipv4_address(params["synchronizetoip"]):
            self.module.fail_json(msg=f'synchronizetoip is not a valid ip address: {params["synchronizetoip"]}')
        if params["pfsyncinterface"] is not None and not self.pfsense.is_interface_display_name(params["pfsyncinterface"]):
            self.module.fail_json(msg=f'pfsyncinterface is not a valid display name of interface: {params["pfsyncinterface"]}')

    ##############################
    # XML processing
    #
    def _create_target(self):
        """ create the XML target_elt """
        return self.root_elt

    def _find_target(self):
        """ find the XML target_elt """
        return self.root_elt


    @staticmethod
    def _get_params_to_remove():
        """ returns the list of params to remove if they are not set """
        return ['pfsyncenabled',
                'adminsync',
                'synchronizeusers',
                'synchronizeauthservers',
                'synchronizecerts',
                'synchronizerules',
                'synchronizeschedules',
                'synchronizealiases',
                'synchronizenat',
                'synchronizeipsec',
                'synchronizeopenvpn',
                'synchronizedhcpd',
                'synchronizedhcrelay',
                'synchronizedhcrelay6',
                'synchronizewol',
                'synchronizestaticroutes',
                'synchronizevirtualip',
                'synchronizetrafficshaper',
                'synchronizetrafficshaperlimiter',
                'synchronizednsforwarder',
                'synchronizecaptiveportal']

    ##############################
    # run
    #
    def _update(self):
        """ make the target pfsense reload """
        return self.pfsense.phpshell('''
require_once("interfaces.inc");

/* Updated High Availability Sync configuration */
interfaces_sync_setup();
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

        values += self.format_updated_cli_field(self.obj, before, 'pfsyncenabled', fvalue=self.fvalue_bool, add_comma=(values), log_none=False)
        values += self.format_updated_cli_field(self.obj, before, 'adminsync', fvalue=self.fvalue_bool, add_comma=(values), log_none=False)
        values += self.format_updated_cli_field(self.obj, before, 'synchronizeusers', fvalue=self.fvalue_bool, add_comma=(values), log_none=False)
        values += self.format_updated_cli_field(self.obj, before, 'synchronizeauthservers', fvalue=self.fvalue_bool, add_comma=(values), log_none=False)
        values += self.format_updated_cli_field(self.obj, before, 'synchronizecerts', fvalue=self.fvalue_bool, add_comma=(values), log_none=False)
        values += self.format_updated_cli_field(self.obj, before, 'synchronizerules', fvalue=self.fvalue_bool, add_comma=(values), log_none=False)
        values += self.format_updated_cli_field(self.obj, before, 'synchronizeschedules', fvalue=self.fvalue_bool, add_comma=(values), log_none=False)
        values += self.format_updated_cli_field(self.obj, before, 'synchronizealiases', fvalue=self.fvalue_bool, add_comma=(values), log_none=False)
        values += self.format_updated_cli_field(self.obj, before, 'synchronizenat', fvalue=self.fvalue_bool, add_comma=(values), log_none=False)
        values += self.format_updated_cli_field(self.obj, before, 'synchronizeipsec', fvalue=self.fvalue_bool, add_comma=(values), log_none=False)
        values += self.format_updated_cli_field(self.obj, before, 'synchronizeopenvpn', fvalue=self.fvalue_bool, add_comma=(values), log_none=False)
        values += self.format_updated_cli_field(self.obj, before, 'synchronizedhcpd', fvalue=self.fvalue_bool, add_comma=(values), log_none=False)
        values += self.format_updated_cli_field(self.obj, before, 'synchronizedhcrelay', fvalue=self.fvalue_bool, add_comma=(values), log_none=False)
        values += self.format_updated_cli_field(self.obj, before, 'synchronizedhcrelay6', fvalue=self.fvalue_bool, add_comma=(values), log_none=False)
        values += self.format_updated_cli_field(self.obj, before, 'synchronizewol', fvalue=self.fvalue_bool, add_comma=(values), log_none=False)
        values += self.format_updated_cli_field(self.obj, before, 'synchronizestaticroutes', fvalue=self.fvalue_bool, add_comma=(values), log_none=False)
        values += self.format_updated_cli_field(self.obj, before, 'synchronizevirtualip', fvalue=self.fvalue_bool, add_comma=(values), log_none=False)
        values += self.format_updated_cli_field(self.obj, before, 'synchronizetrafficshaper', fvalue=self.fvalue_bool, add_comma=(values), log_none=False)
        values += self.format_updated_cli_field(self.obj, before, 'synchronizetrafficshaperlimiter', fvalue=self.fvalue_bool, add_comma=(values), log_none=False)
        values += self.format_updated_cli_field(self.obj, before, 'synchronizednsforwarder', fvalue=self.fvalue_bool, add_comma=(values), log_none=False)
        values += self.format_updated_cli_field(self.obj, before, 'synchronizecaptiveportal', fvalue=self.fvalue_bool, add_comma=(values), log_none=False)
        values += self.format_updated_cli_field(self.obj, before, 'pfsyncpeerip', add_comma=(values), log_none=False)
        values += self.format_updated_cli_field(self.obj, before, 'pfsyncinterface', add_comma=(values), log_none=False)
        values += self.format_updated_cli_field(self.obj, before, 'synchronizetoip', add_comma=(values), log_none=False)
        values += self.format_updated_cli_field(self.obj, before, 'username', add_comma=(values), log_none=False)
        values += self.format_updated_cli_field(self.obj, before, 'password', add_comma=(values), log_none=False)
        return values



def main():
    module = AnsibleModule(
        argument_spec=HASYNC_ARGUMENT_SPEC,
        required_if=hasync_REQUIRED_IF,
        supports_check_mode=True)

    pfmodule = PFSenseHasyncModule(module)
    pfmodule.run(module.params)
    pfmodule.commit_changes()


if __name__ == '__main__':
    main()
