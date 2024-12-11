import re
import json
import requests

# Function to parse Cisco configuration
def parse_cisco_config(config):
    parsed_data = {}

    # Extract hostname
    match_hostname = re.search(r'hostname\s+(\S+)', config)
    if match_hostname:
        parsed_data['hostname'] = match_hostname.group(1)

    # Extract interfaces with descriptions and IP addresses
    interfaces = []
    for match_intf in re.finditer(r'interface\s+(\S+)\s*([\s\S]*?)(?=interface|\Z)', config):
        intf_name = match_intf.group(1)
        description = re.search(r'description\s+(.*)', match_intf.group(2))
        ip_address = re.search(r'ip address\s+([\d.]+)\s+([\d.]+)', match_intf.group(2))
        ipv6_address = re.search(r'ipv6 address\s+([\da-fA-F:]+)\/(\d+)', match_intf.group(2))

        interface_data = {
            'name': intf_name,
            'description': description.group(1) if description else None,
            'ipv4_address': ip_address.group(1) if ip_address else None,
            'ipv4_subnet_mask': ip_address.group(2) if ip_address else None,
            'ipv6_address': ipv6_address.group(1) if ipv6_address else None,
            'ipv6_prefix_length': ipv6_address.group(2) if ipv6_address else None
        }
        interfaces.append(interface_data)
    parsed_data['interfaces'] = interfaces

    # Extract VLANs
    vlans = []
    for match_vlan in re.finditer(r'vlan\s+(\d+)\s*\n\s*name\s+([^\n]+)', config):
        vlan_data = {
            'id': match_vlan.group(1),
            'name': match_vlan.group(2)
        }
        vlans.append(vlan_data)
    parsed_data['vlans'] = vlans

    return parsed_data

# Function to push data to Nautobot
def push_to_nautobot(data):
    nautobot_url = 'http://localhost:8000/api/'
    token = 'dadab498fca1ef6b3e221c2e9b4cc81dc1f3e1f4'

    headers = {
        'Content-Type': 'application/json',
        'Authorization': f'Token {token}',
    }

    # Example data structure for pushing to Nautobot's dcim/devices endpoint
    nautobot_data = {
        'name': data['hostname'],
        'device_type': 'switch',
        'platform': 'Cisco IOS XE',  # Adjust according to your platform
        'interfaces': data['interfaces'],
        'vlans': data['vlans'],
        # Add more fields as needed based on Nautobot's dcim/devices API requirements
    }

    try:
        response = requests.post(f'{nautobot_url}dcim/devices/', headers=headers, data=json.dumps(nautobot_data))
        response.raise_for_status()  # Raise an error for non-2xx responses
        print('Device data successfully pushed to Nautobot!')
    except requests.exceptions.RequestException as e:
        print(f'Error pushing data to Nautobot: {e}')

# Example Cisco configuration (replace with your actual configuration)
cisco_config = """
Building configuration...

Current configuration : 7333 bytes
!
! Last configuration change at 18:18:56 UTC Mon Jul 8 2024
!
version 17.12
service timestamps debug datetime msec
service timestamps log datetime msec
service call-home
platform qfp utilization monitor load 80
platform punt-keepalive disable-kernel-core
platform sslvpn use-pd
platform console virtual
!
hostname cat8000v
!
boot-start-marker
boot system bootflash:packages.conf
boot-end-marker
!
!
aaa new-model
!
!
aaa authentication login default local
aaa authorization exec default local
!
!
aaa session-id common
!
!
!
!
!
!
!
!
!
!
!
!
ip domain name cisco.com
!
!
!
login on-success log
!
!
subscriber templating
vtp version 1
multilink bundle-name authenticated
!
pae
!
!
crypto pki trustpoint TP-self-signed-3209586145
 enrollment selfsigned
 subject-name cn=IOS-Self-Signed-Certificate-3209586145
 revocation-check none
 rsakeypair TP-self-signed-3209586145
 hash sha256
!
crypto pki trustpoint SLA-TrustPoint
 enrollment pkcs12
 revocation-check crl
 hash sha256
!
!
crypto pki certificate chain TP-self-signed-3209586145
 certificate self-signed 01
  30820330 30820218 A0030201 02020101 300D0609 2A864886 F70D0101 05050030
  31312F30 2D060355 04031326 494F532D 53656C66 2D536967 6E65642D 43657274
  69666963 6174652D 33323039 35383631 3435301E 170D3233 30323237 30353137
  31325A17 0D333330 32323630 35313731 325A3031 312F302D 06035504 03132649
  4F532D53 656C662D 5369676E 65642D43 65727469 66696361 74652D33 32303935
  38363134 35308201 22300D06 092A8648 86F70D01 01010500 0382010F 00308201
  0A028201 0100DA9D D10B2672 974416C2 BC4F4132 DF8DD724 13BE2BBA 3A40F21C
  DA8F647F B7379A91 B23A9F25 8C617395 7B2180E6 1FB61195 1E8535E0 578CD897
  11064E3D 40245DC7 955D0F73 29A72D39 7B50A9E5 6997F18F 9A7671D8 96570923
  A4E5D707 623C1774 AD82B10D 73FA170E 4446E280 0012BDB9 F99BC0E4 20BBA9A3
  8479A67D 5C6D358D D90F34E0 E29BA5E8 07040A4B 9F3D7D29 5595C364 DAE77930
  8885165F E6C35D15 5EF140F7 B22D01FF 95A19026 EDDA92F3 7325B5C7 E3F814B0
  7979AB73 D180D8AF CC2BAB70 27145DC4 589EE4B6 4AB09F58 C284E219 75E27BB8
  5FC33333 26226C02 2A94B628 3F82A41C F5181EA6 F59784E5 45194C3B 8D3B6E9C
  79CC8359 8B910203 010001A3 53305130 0F060355 1D130101 FF040530 030101FF
  301F0603 551D2304 18301680 14ADE170 B53AA3EC 4C9154DE 1A4CE02B 2E83E88D
  D9301D06 03551D0E 04160414 ADE170B5 3AA3EC4C 9154DE1A 4CE02B2E 83E88DD9
  300D0609 2A864886 F70D0101 05050003 82010100 1BBBC609 17446925 5F13E8F0
  85428490 B6E9B9FE 8426798C 7B3699FA C66709D3 E560DD18 0EB98574 506E99F6
  E03C0CBC 1D118C1D D0A3E143 1F9D3473 59985621 FE22D26C 066F0824 FADAC2C4
  A43B9A68 2CD88E7B B5A76205 1CB38F6A 85A3FAE9 661D1AFA E2E97243 A020E04F
  070DE776 70F7271F 9ABD35C8 D00F8432 B3E4A924 7D65B2CB 6FB273F8 F0AE783A
  DE8C6523 509AAA89 E960A434 AE2FBABA F4B6EAC5 99DA4EE1 BBB40C62 58CA607B
  8D8FB003 AB964481 F3F9B10B 3C0864F3 A2C139FC BCA45FA6 7EAA308F 6FBDFCEA
  075A3FF1 E0B025A8 1026C01B 630581
  quit
!
!
!
!
!
!
!
!
!
!
!
!
!
!
!
!
interface GigabitEthernet0/0
 description WAN Interface
 ip address 192.168.1.1 255.255.255.0
 ipv6 address 2001:db8::1/64
!
interface GigabitEthernet0/1
 description LAN Interface
 ip address 10.0.0.1 255.255.255.0
 ipv6 address 2001:db8:1::1/64
!
interface GigabitEthernet0/2
 description DMZ Interface
 ip address 172.16.0.1 255.255.255.0
 ipv6 address 2001:db8:2::1/64
!
interface Vlan10
 description Management VLAN
 ip address 192.168.10.1 255.255.255.0
!
interface Vlan20
 description Employee VLAN
 ip address 10.10.20.1 255.255.255.0
!
interface Vlan30
 description Guest VLAN
 ip address 192.168.30.1 255.255.255.0
!
router ospf 1
 network 192.168.1.0 0.0.0.255 area 0
 network 10.0.0.0 0.255.255.255 area 0
 network 172.16.0.0 0.0.0.255 area 0
 network 192.168.10.0 0.0.0.255 area 0
 network 10.10.20.0 0.0.0.255 area 0
 network 192.168.30.0 0.0.0.255 area 0
!
ip forward-protocol nd
!
!
no ip http server
no ip http secure-server
!
!
!
!
control-plane
!
!
line con 0
 exec-timeout 0 0
 privilege level 15
 logging synchronous
 stopbits 1
line aux 0
 exec-timeout 0 0
 privilege level 15
 logging synchronous
 stopbits 1
line vty 0 4
 login local
 transport input ssh
!
end
"""

# Example usage to parse the configuration
parsed_data = parse_cisco_config(cisco_config)
print("Parsed Cisco Configuration:")
print(json.dumps(parsed_data, indent=4))  # This will print the parsed data for verification

# Function to push data to Nautobot
def push_to_nautobot(data):
    nautobot_url = 'http://localhost:8000/api/'
    token = 'dadab498fca1ef6b3e221c2e9b4cc81dc1f3e1f4'

    headers = {
        'Content-Type': 'application/json',
        'Authorization': f'Token {token}',
    }

    # Example data structure for pushing to Nautobot's dcim/devices endpoint
    nautobot_data = {
        'name': data['hostname'],
        'device_type': 'switch',
        'platform': 'Cisco IOS XE',  # Adjust according to your platform
        'interfaces': data['interfaces'],
        'vlans': data['vlans'],
        # Add more fields as needed based on Nautobot's dcim/devices API requirements
    }

    try:
        response = requests.post(f'{nautobot_url}dcim/devices/', headers=headers, data=json.dumps(nautobot_data))
        response.raise_for_status()  # Raise an error for non-2xx responses
        print('Device data successfully pushed to Nautobot!')
    except requests.exceptions.RequestException as e:
        print(f'Error pushing data to Nautobot: {e}')

# Example usage to push data to Nautobot
push_to_nautobot(parsed_data)