# -*- coding: utf-8 -*-

# Copyright: (c) 2021, Chris Liu <chris.liu.hk@icloud.com>
# GNU General Public License v3.0+ (see COPYING or https://www.gnu.org/licenses/gpl-3.0.txt)

from __future__ import absolute_import, division, print_function
import base64
import os
__metaclass__ = type
from ansible_collections.pfsensible.core.plugins.module_utils.module_base import PFSenseModuleBase
from ansible.module_utils.basic import AnsibleModule

OPENVPN_ARGUMENT_SPEC = dict(
    state=dict(default='present', choices=['present', 'absent']),

    mode=dict(default='server_user', options=['p2p_tls','p2p_shared_key', 'server_tls', 'server_user', 'server_tls_user']),
    authmode=dict(required=True, type='list', elements='str'),
    protocol=dict(default='UDP4', options=['UDP4', 'UDP6', 'TCP4', 'TCP6', 'UDP', 'TCP']),
    dev_mode=dict(default='tun', options=['tun', 'tap']),
    if_descr=dict(required=True, type='str'),
    ipaddr=dict(default='', type='str'),
    local_port=dict(default=1194, type='int'),
    descr=dict(required=True, type='str'),
    custom_options=dict(default='', type='str'),
    tls=dict(required=True, type='str'),
    tls_type=dict(default='auth', options=['auth', 'crypt']),
    tlsauth_keydir=dict(default='default', options=['default', '0', '1', '2']),
    ca_descr=dict(required=True, type='str'),
    crlref=dict(default='', type='str'), # todo
    ocspurl=dict(default='', type='str'),
    cert_descr=dict(required=True, type='str'),
    dh_length=dict(default="2048", choices=["1024","2048","3072","4096","6144","7680","8192","15360","16384",'none']),
    ecdh_curve=dict(default='none', choices=['prime256v1', 'secp384r1', 'secp521r1','none']),
    cert_depth=dict(default='1', choices=['1','2','3','4','5']),
    data_ciphers_fallback=dict(default='AES-256-CBC', type='str'),
    digest=dict(default='SHA256', type='str'),
    engine=dict(default='none', type='str'),
    tunnel_network=dict(required=True, type='str'),
    remote_network=dict(default='', type='str'),
    gwredir=dict(default=False, type='bool'),
    local_network=dict(required=True, type='list', elements='str'),
    maxclients=dict(default=0, type='int'), # 0 means no limit
    allow_compression=dict(default='no', choices=['yes', 'no', 'asym']),
    compression=dict(default='', choices=['','none','stub','stub-v2', 'lz4', 'lz4-v2', 'lzo', 'noadapt', 'adaptive', 'yes', 'no']),
    compression_push=dict(default=False, type='bool'),
    passtos=dict(default=False, type='bool'),
    client2client=dict(default=False, type='bool'),
    dynamic_ip=dict(default=False, type='bool'),
    topology=dict(default='subnet', choices=['subnet', 'net30']),
    serverbridge_dhcp=dict(default=False, type='bool'),
    serverbridge_if_descr=dict(default='', type='str'),
    serverbridge_routegateway=dict(default='', type='str'),
    serverbridge_dhcp_start=dict(default='', type='str'),
    serverbridge_dhcp_end=dict(default='', type='str'),
    username_as_common_name=dict(default=True, type='bool'),
    exit_notify=dict(default='1', choices=['none', '1', '2']),
    sndrcvbuf=dict(default='0', choices=['0', str(64*1024), str(128*1024), str(256*1024), str(512*1024), str(1*1024^2), str(2*1024^2)]),
    netbios_enable=dict(default=False, type='bool'),
    netbios_ntype=dict(default='none', choices=['none', 'b-node', 'p-node', 'm-node', 'h-node']),
    netbios_scope=dict(default='', type='str'),
    create_gw=dict(default='both', choices=['v4only', 'v6only', 'both']),
    verbosity_level=dict(default=1, type='int'),
    data_ciphers=dict(default=['AES-256-GCM','AES-128-GCM','CHACHA20-POLY1305'], type='list', elements='str'),
    ncp_enable=dict(default=False, type='bool'),
    ping_method=dict(default="keepalive", choices=['keepalive', 'ping']),
    keepalive_interval=dict(default=10, type='int'),
    keepalive_timeout=dict(default=60, type='int'),
    ping_seconds=dict(default=10, type='int'),
    ping_push=dict(default=False, type='bool'),
    ping_action=dict(default='ping_restart', choices=['ping_restart', 'ping_exit']),
    ping_action_seconds=dict(default=60, type='int'),
    ping_action_push=dict(default=False, type='bool'),
    inactive_seconds=dict(default=0, type='int'),
    dns_domain=dict(default='', type='str'),
    dns_server1=dict(default='', type='str'),
    dns_server2=dict(default='', type='str'),
    dns_server3=dict(default='', type='str'),
    dns_server4=dict(default='', type='str'),
    duplicate_cn=dict(default=False, type='bool')
)


OPENVPN_REQUIRED_IF = []


class PFSenseOpenVpnModule(PFSenseModuleBase):
    """ module managing pfsense OPENVPNs """

    @staticmethod
    def get_argument_spec():
        """ return argument spec """
        return OPENVPN_ARGUMENT_SPEC

    ##############################
    # init
    #
    def __init__(self, module, pfsense=None):
        super(PFSenseOpenVpnModule, self).__init__(module, pfsense)
        self.name = "pfsense_openvpn"

        self.before_dev_mode = None
        self.id = None

    def _params_to_obj(self):
        """ return a dict from module params """
        params = self.params

        obj = dict()

        if params["state"] == "present":
            self._get_ansible_param(obj, "mode")
            obj["authmode"] = ','.join(params["authmode"])
            self._get_ansible_param(obj, "protocol")
            self._get_ansible_param(obj, "dev_mode")
            if params["if_descr"] != "any":
                obj["interface"] = self.pfsense.get_interface_by_display_name(params["if_descr"])
            else:
                obj["interface"] = "any"
            self._get_ansible_param(obj, "ipaddr")
            self._get_ansible_param(obj, "local_port")
            self._get_ansible_param(obj, "descr", fname="description")
            self._get_ansible_param(obj, "custom_options")
            obj["tls"] = base64.b64encode(bytes(params['tls'],'utf-8')).decode()
            self._get_ansible_param(obj, "tls_type")
            self._get_ansible_param(obj, "tlsauth_keydir")
            obj["caref"] = self.pfsense.get_caref(params["ca_descr"])
            self._get_ansible_param(obj, "crlref")
            self._get_ansible_param(obj, "ocspurl")
            obj["certref"] = self.pfsense.find_cert_elt(params["cert_descr"]).find("refid").text
            self._get_ansible_param(obj, "dh_length")
            self._get_ansible_param(obj, "ecdh_curve")
            self._get_ansible_param(obj, "cert_depth")
            self._get_ansible_param(obj, "data_ciphers_fallback")
            self._get_ansible_param(obj, "digest")
            self._get_ansible_param(obj, "engine")
            self._get_ansible_param(obj, "tunnel_network")
            self._get_ansible_param(obj, "remote_network")
            self._get_ansible_param_bool(obj, "gwredir")
            obj["local_network"] = ','.join(params["local_network"])
            if not params["maxclients"]:
                obj["maxclients"] = ''
            else:
                self._get_ansible_param(obj, "maxclients")
            self._get_ansible_param(obj, "allow_compression")
            self._get_ansible_param(obj, "compression")
            self._get_ansible_param_bool(obj, "compression_push")
            self._get_ansible_param_bool(obj, "passtos")
            self._get_ansible_param_bool(obj, "client2client")
            self._get_ansible_param_bool(obj, "dynamic_ip")
            self._get_ansible_param(obj, "topology")
            self._get_ansible_param_bool(obj, "serverbridge_dhcp")
            obj["serverbridge_interface"] = self.pfsense.get_interface_by_display_name(params["serverbridge_if_descr"])
            self._get_ansible_param(obj, "serverbridge_routegateway")
            self._get_ansible_param(obj, "serverbridge_dhcp_start")
            self._get_ansible_param(obj, "serverbridge_dhcp_end")
            if params["username_as_common_name"]:
                obj["username_as_common_name"] = "enabled"
            else:
                obj["username_as_common_name"] = "disabled"
            self._get_ansible_param(obj, "exit_notify")
            if not params["sndrcvbuf"]:
                obj["sndrcvbuf"] = ""
            else:
                obj["sndrcvbuf"] = params["sndrcvbuf"]
            self._get_ansible_param_bool(obj, "netbios_enable")
            obj["netbios_ntype"] = self.get_netbios_ntype_key(params["netbios_ntype"])
            self._get_ansible_param(obj, "netbios_scope")
            self._get_ansible_param(obj, "create_gw")
            self._get_ansible_param(obj, "verbosity_level")
            obj["data_ciphers"] = ','.join(params["data_ciphers"])
            self._get_ansible_param_bool(obj, "ncp_enable")
            self._get_ansible_param(obj, "ping_method")
            self._get_ansible_param(obj, "keepalive_interval")
            self._get_ansible_param(obj, "keepalive_timeout")
            self._get_ansible_param(obj, "ping_seconds")
            self._get_ansible_param_bool(obj, "ping_push")
            self._get_ansible_param(obj, "ping_action")
            self._get_ansible_param(obj, "ping_action_seconds")
            self._get_ansible_param_bool(obj, "ping_action_push")
            self._get_ansible_param(obj, "inactive_seconds")
            self._get_ansible_param(obj, "dns_domain")
            self._get_ansible_param(obj, "dns_server1")
            self._get_ansible_param(obj, "dns_server2")
            self._get_ansible_param(obj, "dns_server3")
            self._get_ansible_param(obj, "dns_server4")
            self._get_ansible_param_bool(obj, "duplicate_cn")
        else:
            obj["disable"] = ""
        return obj

    def get_netbios_ntype_key(self, value):
        if value == 'none':
            return 0
        elif value == 'b-node':
            return 1
        elif value == 'p-node':
            return 2
        elif value == 'm-node':
            return 4
        elif value == 'h-node':
            return 8
        return None

    def get_digests(self):
        return self.pfsense.php("""
require_once("openvpn.inc");
echo json_encode(array_keys(openvpn_get_digestlist()));
""")

    def get_ciphers(self):
        return self.pfsense.php("""
require_once("openvpn.inc");
echo json_encode(array_keys(openvpn_get_cipherlist()));
""") 
    def get_auth_servers(self):
        return self.pfsense.php("""
require_once("auth.inc");
echo json_encode(array_keys(auth_get_authserver_list()));
""") 

    def get_engine(self):
        return self.pfsense.php("""
require_once("openvpn.inc");
echo json_encode(array_keys(openvpn_get_engines()));
""") 

    def get_next_vpnid(self):
        return self.pfsense.php("""
require_once("openvpn.inc");
echo json_encode(array('vpnid'=>openvpn_vpnid_next()));
""")['vpnid']

    def _validate_params(self):

        digess = self.get_digests()
        ciphers = self.get_ciphers()

        """ do some extra checks on input parameters """
        params = self.params
        
        for authmode in params["authmode"]:
            if not authmode in self.get_auth_servers():
                self.module.fail_json(msg=f'authmode, {authmode} is not a valid auth')
        
        if params["if_descr"]!="any" and not self.pfsense.is_interface_display_name(params["if_descr"]):
            self.module.fail_json(msg=f'if_descr, {params["if_descr"]} is not a display name of interface')

        if not self.pfsense.is_ipv4_address(params["ipaddr"]) and params["ipaddr"]!='':
            self.module.fail_json(msg=f'ipaddr, {params["ipaddr"]} is not a valid ipv4 address')
        
        if not self.pfsense.get_caref(params["ca_descr"]):
            self.module.fail_json(msg=f'ca_descr, {params["ca_descr"]} is not a valid descr of CA')
        
        if not self.pfsense.find_cert_elt(params["cert_descr"]):
            self.module.fail_json(msg=f'cert_descr, {params["cert_descr"]} is not a valid descr of cert')
        
        if not params["data_ciphers_fallback"] in ciphers:
            self.module.fail_json(msg=f'data_ciphers_fallback, {params["data_ciphers_fallback"]} is not a valid ciphers')

        if not params["digest"] in self.get_digests():
            self.module.fail_json(msg=f'digest, {params["digest"]} is not a valid digest')

        if not params["engine"] in self.get_engine():
            self.module.fail_json(msg=f'engine, {params["engine"]} is not a valid engine')

        if not self.pfsense.is_ipv4_network(params["tunnel_network"]) and params["tunnel_network"]!='':
            self.module.fail_json(msg=f'tunnel_network, {params["tunnel_network"]} is not a valid ipv4 network')

        if not self.pfsense.is_ipv4_network(params["remote_network"]) and params["remote_network"]!='':
            self.module.fail_json(msg=f'remote_network, {params["remote_network"]} is not a valid ipv4 network')
        
        for local_network in params["local_network"]:
            if not self.pfsense.is_ipv4_network(local_network) and local_network!='':
                self.module.fail_json(msg=f'local_network, {local_network} is not a valid ipv4 network')
        
        if self.get_netbios_ntype_key(params["netbios_ntype"]) is None:
            self.module.fail_json(msg=f'netbios_ntype, {params["netbios_ntype"]} is not a valid')

        for cipher in params["data_ciphers"]:
            if not cipher in ciphers:
                self.module.fail_json(msg=f'data_ciphers, {params["data_ciphers"]} is not a valid ciphers')

    ##############################
    # XML processing
    #

    def _find_target(self):
        """ find the XML target_elt """
        obj = self.obj
        
        openvpn_elt = self.pfsense.get_element("openvpn", create_node=True)
        
        target_elt=None
        for idx, elt in enumerate(openvpn_elt.findall("openvpn-server")):
            if obj["description"] == elt.find("description").text:
                target_elt = elt
                self.before_dev_mode = elt.find("dev_mode").text
                self.id = idx
        
        if self.id is None:
            self.id = len(openvpn_elt.findall("openvpn-server"))
        
        if not target_elt:
            target_elt = self.pfsense.new_element("openvpn-server")
            openvpn_elt.append(target_elt)
            self.obj["vpnid"] = self.get_next_vpnid()

        return target_elt

    def _get_params_to_remove(self):
        """ returns the list of params to remove if they are not set """
        return []

    ##############################
    # run
    #
    def _update(self):
        """ make the target pfsense reload, copy from https://github.com/pfsense/pfsense/blob/master/src/usr/local/www/vpn_openvpn_server.php"""
        cleanup_stat = ''
        if self.before_dev_mode and self.before_dev_mode != self.obj["dev_mode"]:
            cleanup_stat = f"openvpn_delete('server', {self.obj['vpnid']});"
        return self.pfsense.phpshell('''
require_once("openvpn.inc");
require_once("pfsense-utils.inc");
require_once("pkg-utils.inc");
require_once("services.inc");

init_config_arr(array('openvpn', 'openvpn-server'));
$a_server = &$config['openvpn']['openvpn-server'];

'''+
cleanup_stat+
f'''
$server = $a_server[{self.id}];
openvpn_resync('server', $server);
openvpn_resync_csc_all();
services_unbound_configure();
''')

    ##############################
    # Logging
    #
    def _get_obj_name(self):
        """ return obj's name """
        return self.name

    def _log_fields(self, before=None):
        """ generate pseudo-CLI command fields parameters to create an obj """
        return ''



def main():
    module = AnsibleModule(
        argument_spec=OPENVPN_ARGUMENT_SPEC,
        required_if=OPENVPN_REQUIRED_IF,
        supports_check_mode=True)

    pfmodule = PFSenseOpenVpnModule(module)
    pfmodule.run(module.params)
    pfmodule.commit_changes()


if __name__ == '__main__':
    main()
