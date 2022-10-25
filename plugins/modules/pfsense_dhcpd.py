# -*- coding: utf-8 -*-

# Copyright: (c) 2021, Chris Liu <chris.liu.hk@icloud.com>
# GNU General Public License v3.0+ (see COPYING or https://www.gnu.org/licenses/gpl-3.0.txt)

# TODO: advance page of DHCPD and access control is not done here
# TODO: alias for DHCPD record

from __future__ import absolute_import, division, print_function
import copy
import re
__metaclass__ = type
from ansible_collections.pfsensible.core.plugins.module_utils.module_base import PFSenseModuleBase
from ansible.module_utils.basic import AnsibleModule


DHCPD_RANGE_SPEC = dict(
    ip_from=dict(required=True, type='str'),
    ip_to=dict(required=True, type='str'),
)

DHCPD_STATICMAP_SPEC = dict(
    mac=dict(required=True, type='str'),
    cid=dict(default='', type='str'),
    ipaddr=dict(default='', type='str'),
    hostname=dict(default='', type='str'),
    descr=dict(required=True, type='str'),
    defaultleasetime=dict(default=7200, type='int'),
    maxleasetime=dict(default=86400, type='int'),
    gateway=dict(default='', type='str'),
    domain=dict(default='', type='str'),
    domainsearchlist=dict(default='', type='str'),
    ddnsdomain=dict(default='', type='str'),
    ddnsdomainprimary=dict(default='', type='str'),
    ddnsdomainsecondary=dict(default='', type='str'),
    ddnsdomainkeyname=dict(default='', type='str'),
    ddnsdomainkeyalgorithm=dict(default='hmac-md5', choices=['hmac-md5', 'hmac-sha1', 'hmac-sha224', 'hmac-sha256', 'hmac-sha384', 'hmac-sha512']),
    ddnsdomainkey=dict(default='', type='str'),
    tftp=dict(default='', type='str'),
    ldap=dict(default='', type='str'),
    nextserver=dict(default='', type='str'),
    filename=dict(default='', type='str'),
    filename32=dict(default='', type='str'),
    filename64=dict(default='', type='str'),
    filename32arm=dict(default='', type='str'),
    filename64arm=dict(default='', type='str'),
    rootpath=dict(default='', type='str'),
    numberoptions=dict(default='', type='str'),
)

DHCPD_ARGUMENT_SPEC = dict(
    state=dict(default='present', choices=['present', 'absent']),

    if_descr=dict(required=True, type='str'),
    ip_range=dict(required=True, type='dict', options=DHCPD_RANGE_SPEC),
    failover_peerip=dict(default='', type='str'),
    dhcpleaseinlocaltime=dict(default=False, type='bool'),
    defaultleasetime=dict(default=7200, type='int'),
    maxleasetime=dict(default=86400, type='int'),
    netmask=dict(default='', type='str'),
    gateway=dict(default='', type='str'),
    domain=dict(default='', type='str'),
    domainsearchlist=dict(default='', type='str'),
    ddnsdomain=dict(default='', type='str'),
    ddnsdomainprimary=dict(default='', type='str'),
    ddnsdomainsecondary=dict(default='', type='str'),
    ddnsdomainkeyname=dict(default='', type='str'),
    ddnsdomainkeyalgorithm=dict(default='hmac-md5', choices=['hmac-md5', 'hmac-sha1', 'hmac-sha224', 'hmac-sha256', 'hmac-sha384', 'hmac-sha512']),
    ddnsdomainkey=dict(default='', type='str'),
    mac_allow=dict(default='', type='str'),
    mac_deny=dict(default='', type='str'),
    ddnsclientupdates=dict(default='allow', choices=['allow', 'deny', 'ignore']),
    tftp=dict(default='', type='str'),
    ldap=dict(default='', type='str'),
    nextserver=dict(default='', type='str'),
    filename=dict(default='', type='str'),
    filename32=dict(default='', type='str'),
    filename64=dict(default='', type='str'),
    filename32arm=dict(default='', type='str'),
    filename64arm=dict(default='', type='str'),
    rootpath=dict(default='', type='str'),
    numberoptions=dict(default='', type='str'),
    dnsserver=dict(default=[], type='list', elements='str'),
    staticmap=dict(default=[], type='list', elements='dict', options=DHCPD_STATICMAP_SPEC),
    netboot=dict(default=False, type='bool')
)

DHCPD_REQUIRED_IF = []


class PFSenseDHCPDModule(PFSenseModuleBase):
    """ module managing pfsense DHCPDs """

    @staticmethod
    def get_argument_spec():
        """ return argument spec """
        return DHCPD_ARGUMENT_SPEC

    ##############################
    # init
    #
    def __init__(self, module, pfsense=None):
        super(PFSenseDHCPDModule, self).__init__(module, pfsense)
        self.name = "pfsense_dhcpd"

        self.root_elt = self.pfsense.get_element('dhcpd')
    
    def _range_params_to_obj(self, params):
        obj = dict()
        obj["from"] = params["ip_from"]
        obj["to"] = params["ip_to"]
        return obj

    def _staticmap_to_obj(self, params):
        obj = dict()
        obj["mac"] = params["mac"]
        obj["cid"] = params["cid"]
        obj["ipaddr"] = params["ipaddr"]
        obj["hostname"] = params["hostname"]
        obj["descr"] = params["descr"]
        obj["defaultleasetime"] = str(params["defaultleasetime"])
        obj["maxleasetime"] = str(params["maxleasetime"])
        obj["gateway"] = params["gateway"]
        obj["domain"] = params["domain"]
        obj["domainsearchlist"] = params["domainsearchlist"]
        obj["ddnsdomain"] = params["ddnsdomain"]
        obj["ddnsdomainprimary"] = params["ddnsdomainprimary"]
        obj["ddnsdomainsecondary"] = params["ddnsdomainsecondary"]
        obj["ddnsdomainkeyname"] = params["ddnsdomainkeyname"]
        obj["ddnsdomainkeyalgorithm"] = params["ddnsdomainkeyalgorithm"]
        obj["ddnsdomainkey"] = params["ddnsdomainkey"]
        obj["tftp"] = params["tftp"]
        obj["ldap"] = params["ldap"]
        obj["nextserver"] = params["nextserver"]
        obj["filename"] = params["filename"]
        obj["filename32"] = params["filename32"]
        obj["filename64"] = params["filename64"]
        obj["filename32arm"] = params["filename32arm"]
        obj["filename64arm"] = params["filename64arm"]
        obj["rootpath"] = params["rootpath"]
        obj["numberoptions"] = params["numberoptions"]
        return obj

    def _params_to_obj(self):
        """ return a dict from module params """
        params = self.params

        obj = dict()

        if params["state"] == "present":
            obj["enable"] = ""
            obj["range"] = self._range_params_to_obj(params["ip_range"])
            self._get_ansible_param(obj, "failover_peerip")
            self._get_ansible_param_bool(obj, "dhcpleaseinlocaltime", value='yes')
            self._get_ansible_param(obj, "defaultleasetime")
            self._get_ansible_param(obj, "maxleasetime")
            self._get_ansible_param(obj, "netmask")
            self._get_ansible_param(obj, "gateway")
            self._get_ansible_param(obj, "domain")
            self._get_ansible_param(obj, "domainsearchlist")
            self._get_ansible_param(obj, "ddnsdomain")
            self._get_ansible_param(obj, "ddnsdomainprimary")
            self._get_ansible_param(obj, "ddnsdomainsecondary")
            self._get_ansible_param(obj, "ddnsdomainkeyname")
            self._get_ansible_param(obj, "ddnsdomainkeyalgorithm")
            self._get_ansible_param(obj, "ddnsdomainkey")
            self._get_ansible_param(obj, "mac_allow")
            self._get_ansible_param(obj, "mac_deny")
            self._get_ansible_param(obj, "ddnsclientupdates")
            self._get_ansible_param(obj, "tftp")
            self._get_ansible_param(obj, "ldap")
            self._get_ansible_param(obj, "nextserver")
            self._get_ansible_param(obj, "filename")
            self._get_ansible_param(obj, "filename32")
            self._get_ansible_param(obj, "filename64")
            self._get_ansible_param(obj, "filename32arm")
            self._get_ansible_param(obj, "filename64arm")
            self._get_ansible_param(obj, "rootpath")
            self._get_ansible_param(obj, "numberoptions")
            self._get_ansible_param(obj, "dnsserver")
            obj["staticmap"] = [self._staticmap_to_obj(staticmap) for staticmap in params["staticmap"]]
            if(params["netboot"]):
                obj["netboot"]=""
        return obj

    def _validate_ip_range(self, params):
        if not self.pfsense.is_ipv4_address(params["ip_from"]):
            self.module.fail_json(msg=f'ip_from, {params["ip_from"]} is not a valid ipv4 address')
        if not self.pfsense.is_ipv4_address(params["ip_to"]):
            self.module.fail_json(msg=f'ip_to, {params["ip_to"]} is not a valid ipv4 address')
    
    def _validate_staticmap(self, params):
        if not self.pfsense.is_ipv4_address(params["ipaddr"]):
            self.module.fail_json(msg=f'ipaddr, {params["ipaddr"]} is not a valid ipv4 address')
        if params.get('mac') and re.match('^([0-9A-F]{2}[:-]){5}([0-9A-F]{2})$', params['mac'], flags=re.IGNORECASE) is None:
            self.module.fail_json(msg=f'MAC address, {params.get("mac")} , must be in the following format: xx:xx:xx:xx:xx:xx (or blank).')

    def _validate_params(self):
        """ do some extra checks on input parameters """
        params = self.params

        self._validate_ip_range(params["ip_range"])
        
        if params["gateway"] != '' and params["gateway"] != 'none' and not self.pfsense.is_ipv4_address(params["gateway"]):
            self.module.fail_json(msg=f'gateway, {params["gateway"]} is not a valid ipv4 address')

        for dnsserver in params["dnsserver"]:
            if not self.pfsense.is_ipv4_address(dnsserver):
                self.module.fail_json(msg=f'dnsserver, {params["dnsserver"]} is not a valid ipv4 address')

        [self._validate_staticmap(staticmap) for staticmap in params["staticmap"]]

    ##############################
    # XML processing
    #
    def _create_target(self):
        """ create the XML target_elt """
        return self.root_elt

    def _find_target(self):
        """ find the XML target_elt """
        dhcpd_xml_element = self.root_elt
        if not dhcpd_xml_element:
            dhcpd_xml_element = self.pfsense.new_element('dhcpd')
            self.pfsense.root.append(dhcpd_xml_element)
        
        if_id = self.pfsense.get_interface_by_display_name(self.params["if_descr"])
        if not if_id:
            self.module.fail_json(msg=f'if_descr, {self.params["if_descr"]} is not a valid description of if')

        ret  = dhcpd_xml_element.find(if_id)
        if not ret:
            ret = self.pfsense.new_element(if_id)
            dhcpd_xml_element.append(ret)
        
        return ret

    def _get_params_to_remove(self):
        """ returns the list of params to remove if they are not set """
        return ['netboot']

    ##############################
    # run
    #
    def _update(self):
        """ make the target pfsense reload, copy from https://github.com/pfsense/pfsense/blob/master/src/usr/local/www/services_dhcp.php"""
        return self.pfsense.phpshell('''
require_once("filter.inc");
require_once('rrd.inc');
require_once("shaper.inc");
require_once("util.inc");

$changes_applied = true;
$retval = 0;
$retvaldhcp = 0;
$retvaldns = 0;

if (isset($config['dnsmasq']['enable']) && isset($config['dnsmasq']['regdhcpstatic']))	{
    $retvaldns |= services_dnsmasq_configure();
    if ($retvaldns == 0) {
        clear_subsystem_dirty('hosts');
        clear_subsystem_dirty('staticmaps');
    }
} else if (isset($config['unbound']['enable']) && isset($config['unbound']['regdhcpstatic'])) {
    $retvaldns |= services_unbound_configure();
    if ($retvaldns == 0) {
        clear_subsystem_dirty('unbound');
        clear_subsystem_dirty('hosts');
        clear_subsystem_dirty('staticmaps');
    }
} else {
    $retvaldhcp |= services_dhcpd_configure();
    if ($retvaldhcp == 0) {
        clear_subsystem_dirty('staticmaps');
    }
}
/* BIND package - Bug #3710 */
if (!function_exists('is_package_installed')) {
    require_once('pkg-utils.inc');
}
if (is_package_installed('pfSense-pkg-bind') && isset($config['installedpackages']['bind']['config'][0]['enable_bind'])) {
    $reloadbind = false;
    if (is_array($config['installedpackages']['bindzone'])) {
        $bindzone = $config['installedpackages']['bindzone']['config'];
    } else {
        $bindzone = array();
    }
    for ($x = 0; $x < sizeof($bindzone); $x++) {
        $zone = $bindzone[$x];
        if ($zone['regdhcpstatic'] == 'on') {
            $reloadbind = true;
            break;
        }
    }
    if ($reloadbind === true) {
        if (file_exists("/usr/local/pkg/bind.inc")) {
            require_once("/usr/local/pkg/bind.inc");
            bind_sync();
        }
    }
}
filter_configure();
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
        argument_spec=DHCPD_ARGUMENT_SPEC,
        required_if=DHCPD_REQUIRED_IF,
        supports_check_mode=True)

    pfmodule = PFSenseDHCPDModule(module)
    pfmodule.run(module.params)
    pfmodule.commit_changes()


if __name__ == '__main__':
    main()
