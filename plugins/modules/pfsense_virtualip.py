#!/usr/bin/python
# -*- coding: utf-8 -*-

# Copyright: (c) 2018, Frederic Bor <frederic.bor@wanadoo.fr>
# GNU General Public License v3.0+ (see COPYING or https://www.gnu.org/licenses/gpl-3.0.txt)

from __future__ import absolute_import, division, print_function
__metaclass__ = type

ANSIBLE_METADATA = {'metadata_version': '1.1',
                    'status': ['preview'],
                    'supported_by': 'community'}

DOCUMENTATION = """
---
module: pfsense_virtualip
version_added: 0.1.0
author: Frederic Bor (@f-bor)
short_description: Manage pfSense virtualips
description:
  - Manage pfSense virtualips.
notes:
options:
  state:
    description: State in which to leave the virtualip.
    choices: [ "present", "absent" ]
    default: present
    type: str
  descr:
    description: Description (name) for the virtualip.
    required: true
    type: str
  interface_descr:
    description: Network port descr to which assign the virtualip.
    type: str
  vhid:
    description: VHID Group.
    type: int
    default: 1
  advskew:
    description: Advertising skew.
    type: int 
    default: 0
  advbase:
    description: Advertising base
    type: int
    default: 1
  password:
    type: str
  ipv4_address:
    description:
    type: str
  ipv4_prefixlen:
    description:
    type: int
"""

EXAMPLES = """
- name: Add virtualip
  pfsense_virtualip:
    descr: voice
    virtualip: mvneta0.100
    enable: True
"""

RETURN = """
commands:
    description: the set of commands that would be pushed to the remote device (if pfSense had a CLI)
    returned: always
    type: list
    sample: [
        "create virtualip 'voice', port='mvneta0.100', speed_duplex='autoselect', enable='True'",
        "delete virtualip 'voice'"
    ]
"""

from ansible.module_utils.basic import AnsibleModule
from ansible_collections.pfsensible.core.plugins.module_utils.virtualip import (
    PFSenseVirtualipModule,
    virtualip_ARGUMENT_SPEC,
    virtualip_REQUIRED_IF,
    virtualip_MUTUALLY_EXCLUSIVE
)


def main():
    module = AnsibleModule(
        argument_spec=virtualip_ARGUMENT_SPEC,
        required_if=virtualip_REQUIRED_IF,
        mutually_exclusive=virtualip_MUTUALLY_EXCLUSIVE,
        supports_check_mode=True)

    pfmodule = PFSenseVirtualipModule(module)
    pfmodule.run(module.params)
    pfmodule.commit_changes()


if __name__ == '__main__':
    main()
