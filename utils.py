import requests
import json
import re
from ncclient import manager
from netmiko import ConnectHandler

# Utility functions for Cisco Nautobot script

def get_running_config(device):
    print("Connecting to device via CLI using Netmiko...")
    connection = ConnectHandler(**device)
    running_config = connection.send_command("show running-config")
    connection.disconnect()
    return running_config

def get_restconf_data(device):
    print("Connecting to device via RESTCONF...")
    url = f"https://{device['host']}:443/restconf/data/Cisco-IOS-XR-ifmgr-cfg:interface-configurations"
    headers = {
        "Accept": "application/yang-data+json",
    }
    response = requests.get(url, auth=(device['username'], device['password']), headers=headers, verify=False)
    if response.status_code == 200:
        restconf_data = response.json()
        return restconf_data
    else:
        print(f"RESTCONF request failed with status code {response.status_code}")
        return None

def get_netconf_data(device):
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

def parse_running_config(running_config):
    print("Parsing running config...")
    interfaces = {}
    current_interface = None
    for line in running_config.splitlines():
        line = line.strip()
        if line.startswith("interface"):
            current_interface = line.split()[1]
            interfaces[current_interface] = {}
        elif current_interface:
            if line.startswith("description"):
                interfaces[current_interface]["description"] = line.split(" ", 1)[1]
            elif line.startswith("ipv4 address"):
                interfaces[current_interface]["ipv4_address"] = line.split(" ", 2)[1:]
    return {"interfaces": interfaces}

def create_or_update_in_nautobot(endpoint, data):
    print(f"Creating or updating {endpoint} in Nautobot...")
    nautobot_url = f"http://localhost:8000/api/{endpoint}/"
    headers = {
        "Authorization": "Token a2e22503d99e9337ed1e18fdcf8aeb498c224b3f",
        "Content-Type": "application/json",
    }
    try:
        response = requests.post(nautobot_url, headers=headers, json=data)
        if response.status_code == 201:
            print(f"{endpoint.capitalize()} successfully created in Nautobot.")
        elif response.status_code in [200, 204]:
            print(f"{endpoint.capitalize()} successfully updated in Nautobot.")
        else:
            print(f"Failed to create or update {endpoint} in Nautobot. Status code: {response.status_code}")
            print(response.text)
    except requests.exceptions.RequestException as e:
        print(f"An error occurred: {e}")

def push_to_nautobot(data):
    print("Pushing data to Nautobot...")
    nautobot_url = "http://localhost:8000/api/dcim/devices/"
    headers = {
        "Authorization": "Token a2e22503d99e9337ed1e18fdcf8aeb498c224b3f",
        "Content-Type": "application/json",
    }
    print("Payload being sent to Nautobot:")
    print(json.dumps(data, indent=2))
    try:
        response = requests.post(nautobot_url, headers=headers, json=data)
        if response.status_code == 201:
            print("Data successfully pushed to Nautobot.")
        elif response.status_code == 400:
            print("Failed to push data to Nautobot. Status code: 400 - Bad Request")
            print("Response from Nautobot:")
            print(response.text)
        elif response.status_code == 403:
            print("Failed to push data to Nautobot. Status code: 403 - Forbidden")
            print("Please check your API token and permissions.")
        else:
            print(f"Failed to push data to Nautobot. Status code: {response.status_code}")
            print("Response from Nautobot:")
            print(response.text)
    except requests.exceptions.RequestException as e:
        print(f"An error occurred: {e}")

def get_device_id(device_name):
    print(f"Retrieving device ID for {device_name}...")
    nautobot_url = f"http://localhost:8000/api/dcim/devices/?name={device_name}"
    headers = {
        "Authorization": "Token a2e22503d99e9337ed1e18fdcf8aeb498c224b3f",
    }
    try:
        response = requests.get(nautobot_url, headers=headers)
        if response.status_code == 200 and response.json()["count"] == 1:
            return response.json()["results"][0]["id"]
        else:
            print("Device not found or multiple devices with same name exist.")
            return None
    except requests.exceptions.RequestException as e:
        print(f"An error occurred: {e}")
        return None

def push_interfaces_to_nautobot(device_id, interfaces):
    print(f"Pushing interface data for device ID {device_id} to Nautobot...")
    for interface_name, interface_data in interfaces.items():
        interface_payload = {
            "name": interface_name,
            "device": {
                "id": device_id,
                "object_type": "dcim.device",
                "url": f"http://localhost:8000/api/dcim/devices/{device_id}/"
            },
            "description": interface_data.get("description", ""),
            "enabled": True,
            "type": "virtual",  # Set the type to "virtual" for all interfaces
            "status": {
                "id": "3e1a93d4-cef2-4b05-8fb4-838ff0f5efcb"  # Correct status ID for "Active"
            }
        }
        nautobot_url = f"http://localhost:8000/api/dcim/interfaces/"
        headers = {
            "Authorization": "Token a2e22503d99e9337ed1e18fdcf8aeb498c224b3f",
            "Content-Type": "application/json",
        }
        try:
            response = requests.post(nautobot_url, headers=headers, json=interface_payload)
            if response.status_code == 201:
                print(f"Interface {interface_name} successfully created in Nautobot.")
            elif response.status_code == 400 and "already exists" in response.text:
                print(f"Interface {interface_name} already exists. Attempting to update...")
                
                # Fetch the interface ID to update
                existing_interface_url = f"http://localhost:8000/api/dcim/interfaces/?name={interface_name}&device_id={device_id}"
                existing_interface_response = requests.get(existing_interface_url, headers=headers)
                if existing_interface_response.status_code == 200 and existing_interface_response.json()["count"] == 1:
                    interface_id = existing_interface_response.json()["results"][0]["id"]
                    update_url = f"http://localhost:8000/api/dcim/interfaces/{interface_id}/"
                    response = requests.patch(update_url, headers=headers, json=interface_payload)
                    if response.status_code in [200, 204]:
                        print(f"Interface {interface_name} successfully updated in Nautobot.")
                    else:
                        print(f"Failed to update interface {interface_name}. Status code: {response.status_code}")
                        print(response.text)
                else:
                    print(f"Failed to retrieve existing interface ID for {interface_name}. Status code: {existing_interface_response.status_code}")
                    print(existing_interface_response.text)
            else:
                print(f"Failed to create interface {interface_name}. Status code: {response.status_code}")
                print(response.text)
        except requests.exceptions.RequestException as e:
            print(f"An error occurred: {e}")
