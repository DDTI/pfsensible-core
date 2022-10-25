# pfsense_nodeexporter.py
#!/usr/bin/python
# -*- coding: utf-8 -*-

# GNU General Public License v3.0+ (see COPYING or https://www.gnu.org/licenses/gpl-3.0.txt)

from __future__ import absolute_import, division, print_function
__metaclass__ = type

ANSIBLE_METADATA = {'metadata_version': '1.1',
                    'status': ['preview'],
                    'supported_by': 'community'}

from ansible.module_utils.basic import AnsibleModule
from ansible_collections.pfsensible.core.plugins.module_utils.module_base import PFSenseModuleBase

NODEEXPORTER_ARGUMENT_SPEC = dict(
    state=dict(default='present', choices=['present', 'absent']),

    listen_iface_descr=dict(required=True, type='str'),
    listen_port=dict(default=9100, type='int'),
    collectors=dict(default='boottime,cpu,exec,filesystem,loadavg,meminfo,netdev,textfile,time', type='str'),
    extra_flags=dict(default='--log.level=warn', type='str')
)

class PFSenseNodeExporterModule(PFSenseModuleBase):
    def __init__(self, module, pfsense=None):
        super(PFSenseNodeExporterModule, self).__init__(module, pfsense)
        self.name = "pfsense_nodeexporter"
        self.root_elt = self.pfsense.root.find("installedpackages").find("nodeexporter")
        if self.root_elt is None:
            self.root_elt = self.pfsense.new_element('nodeexporter')
            self.pfsense.root.find("installedpackages").append(self.root_elt)

    @staticmethod
    def get_argument_spec():
        """ return argument spec """
        return NODEEXPORTER_ARGUMENT_SPEC

    ##############################
    # params processing
    #
    def _validate_params(self):
        """ do some extra checks on input parameters """
        params = self.params

        self.pfsense.is_interface_display_name(params["listen_iface_descr"])

    def _params_to_obj(self):
        """ return a dict from module params """
        params = self.params

        obj = dict()
        self.obj = obj

        if params['state'] == 'present':
            obj["enable"] = 'on'
        obj["listen_iface"] = self.pfsense.get_interface_by_display_name(params["listen_iface_descr"])
        self._get_ansible_param(obj, 'listen_port')
        self._get_ansible_param(obj, 'collectors')
        self._get_ansible_param(obj, 'extra_flags')
        return obj

    def _get_params_to_remove(self):
        """ returns the list of params to remove if they are not set """
        if self.params['state'] == 'absent':
            return ["enable"]
        else:
            return []

    def _remove(self):
        super(PFSenseNodeExporterModule, self)._remove()
        self.root_elt.append(self.pfsense.new_element("config"))
    ##############################
    # XML processing
    #
    def _find_target(self):
        target_elf = self.root_elt.find("config")
        if target_elf is None:
            target_elf = self.pfsense.new_element("config")
            self.root_elt.append(target_elf)
        return target_elf 

    ##############################
    # Logging
    #
    def _get_obj_name(self):
        """ return obj's name """
        return self.name

    def _log_fields(self, before=None):
        """ generate pseudo-CLI command fields parameters to create an obj """
        values = ''
        return values

    ##############################
    # run
    #
    def _update(self):
        return self.pfsense.phpshell('''
require_once("node_exporter.inc");
node_exporter_sync_config();
        ''')


def main():
    module = AnsibleModule(
        argument_spec=NODEEXPORTER_ARGUMENT_SPEC,
        required_if=[],
        supports_check_mode=True)

    pfmodule = PFSenseNodeExporterModule(module)
    pfmodule.run(module.params)
    pfmodule.commit_changes()


if __name__ == '__main__':
    main()
