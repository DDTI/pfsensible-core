#!/usr/bin/python
# -*- coding: utf-8 -*-

# Copyright: (c) 2018-2020, Orion Poplawski <orion@nwra.com>
# GNU General Public License v3.0+ (see COPYING or https://www.gnu.org/licenses/gpl-3.0.txt)

from __future__ import absolute_import, division, print_function
__metaclass__ = type

ANSIBLE_METADATA = {'metadata_version': '1.1',
                    'status': ['preview'],
                    'supported_by': 'community'}

import base64
import re

from ansible.module_utils.basic import AnsibleModule
from ansible_collections.pfsensible.core.plugins.module_utils.module_base import PFSenseModuleBase

CERT_ARGUMENT_SPEC = dict(
    state=dict(default='present', choices=['present', 'absent']),

    descr=dict(required=True, type='str'),
    type=dict(default='server', type='str'),
    crt=dict(required=True, type='str'),
    prv=dict(required=True, type='str'),
    ca_descr=dict(default=None, type='str')
)

class PFSenseCertModule(PFSenseModuleBase):
    """ module managing pfsense certificertte authorities """

    def __init__(self, module, pfsense=None):
        super(PFSenseCertModule, self).__init__(module, pfsense)
        self.name = "pfsense_cert"
        self.root_elt = self.pfsense.root
        self.certs = self.pfsense.get_elements('cert')

    @staticmethod
    def get_argument_spec():
        """ return argument spec """
        return CERT_ARGUMENT_SPEC

    ##############################
    # params processing
    #
    def _validate_params(self):
        """ do some extra checks on input parameters """
        params = self.params

        if params['state'] == 'present':
            cert = params['crt']
            lines = cert.splitlines()
            if not(lines[0] == '-----BEGIN CERTIFICATE-----' and lines[-1] == '-----END CERTIFICATE-----'):
                self.module.fail_json(msg='Could not recognize cert format: %s' % (cert))
            prv = params['prv']
            lines = prv.splitlines()
            if not(lines[0] == '-----BEGIN PRIVATE KEY-----' and lines[-1] == '-----END PRIVATE KEY-----') and not(lines[0] == '-----BEGIN RSA PRIVATE KEY-----' and lines[-1] == '-----END RSA PRIVATE KEY-----'):
                self.module.fail_json(msg='Could not recognize private key format: %s' % (prv))
            
            if self.params["ca_descr"] and not self.pfsense.find_ca_elt(self.params["ca_descr"]):
                self.module.fail_json(msg=f'Could not find CA with descr, {self.params["ca_descr"]}')


    def _params_to_obj(self):
        """ return a dict from module params """
        params = self.params

        obj = dict()
        self.obj = obj

        if params['state'] == 'present':
            self._get_ansible_param(obj, 'descr')
            self._get_ansible_param(obj, 'type')
            obj["crt"] = base64.b64encode(bytes(params['crt'],'utf-8')).decode()
            obj["prv"] = base64.b64encode(bytes(params['prv'],'utf-8')).decode()
            if self.params["ca_descr"]:
                obj["caref"] = self.pfsense.find_ca_elt(self.params["ca_descr"]).find("refid").text

        return obj

    ##############################
    # XML processing
    #
    def _find_target(self):
        result = self.root_elt.findall("cert[descr='{0}']".format(self.obj['descr']))
        if len(result) == 1:
            return result[0]
        elif len(result) > 1:
            self.module.fail_json(msg='Found multiple certificertte authorities for name {0}.'.format(self.obj['descr']))
        else:
            return None

    def _find_this_cert_index(self):
        return self.certs.index(self.target_elt)

    def _find_last_cert_index(self):
        if len(self.certs):
            return list(self.root_elt).index(self.certs[len(self.certs) - 1])
        else:
            return len(list(self.root_elt))

    def _create_target(self):
        """ create the XML target_elt """
        self.obj['refid'] = self.pfsense.uniqid()
        return self.pfsense.new_element('cert')

    ##############################
    # Logging
    #
    def _get_obj_name(self):
        """ return obj's name """
        return self.obj['descr']

    def _log_fields(self, before=None):
        """ generate pseudo-CLI command fields parameters to create an obj """
        values = ''
        return values

    ##############################
    # run
    #
    def _update(self):
        return self.pfsense.phpshell('')



def main():
    module = AnsibleModule(
        argument_spec=CERT_ARGUMENT_SPEC,
        required_if=[],
        supports_check_mode=True)

    pfmodule = PFSenseCertModule(module)
    pfmodule.run(module.params)
    pfmodule.commit_changes()


if __name__ == '__main__':
    main()
