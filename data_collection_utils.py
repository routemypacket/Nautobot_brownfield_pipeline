import requests
from netmiko import ConnectHandler
from ncclient import manager

def get_running_config(device):
    """
    Connects to a device via SSH using Netmiko and retrieves the running config.
    """
    print("Connecting to device via CLI using Netmiko...")
    connection = ConnectHandler(**device)
    running_config = connection.send_command("show running-config")
    connection.disconnect()
    return running_config

def get_restconf_data(device):
    """
    Connects to a device via RESTCONF and retrieves interface configurations.
    """
    print("Connecting to device via RESTCONF...")
    url = f"https://{device['host']}:443/restconf/data/Cisco-IOS-XR-ifmgr-cfg:interface-configurations"
    headers = {
        "Accept": "application/yang-data+json",
    }
    response = requests.get(url, auth=(device['username'], device['password']), headers=headers, verify=False)
    if response.status_code == 200:
        return response.json()
    else:
        print(f"RESTCONF request failed with status code {response.status_code}")
        return None

def get_netconf_data(device):
    """
    Connects to a device via NETCONF and retrieves the interface information.
    """
    print("Connecting to device via NETCONF...")
    with manager.connect(
        host=device['host'],
        port=830,
        username=device['username'],
        password=device['password'],
        hostkey_verify=False
    ) as m:
        filter = """
        <filter>
            <interfaces xmlns="http://openconfig.net/yang/interfaces"/>
        </filter>
        """
        netconf_response = m.get(filter)
        return netconf_response.xml