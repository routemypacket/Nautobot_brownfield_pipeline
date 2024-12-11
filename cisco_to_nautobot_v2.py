import requests
import json
from netmiko import ConnectHandler
from ncclient import manager
import re

# Device details for Cisco IOS-XR device
device = {
    "device_type": "cisco_ios",
    "host": "sandbox-iosxr-1.cisco.com",
    "username": "admin",
    "password": "C1sco12345",
}

# Step 1: Gather Data via CLI using Netmiko
def get_running_config():
    print("Connecting to device via CLI using Netmiko...")
    connection = ConnectHandler(**device)
    running_config = connection.send_command("show running-config")
    connection.disconnect()
    return running_config

# Step 2: Gather Data via RESTCONF
def get_restconf_data():
    print("Connecting to device via RESTCONF...")
    url = f"https://{device['host']}:443/restconf/data/Cisco-IOS-XR-ifmgr-cfg:interface-configurations"
    headers = {
        "Accept": "application/yang-data+json",
    }
    response = requests.get(url, auth=(device['username'], device['password']), headers=headers, verify=False)
    if response.status_code == 200:
        restconf_data = response.json()
        print("Collected Data via RESTCONF:\n")
        print(json.dumps(restconf_data, indent=2))
        return restconf_data
    else:
        print(f"RESTCONF request failed with status code {response.status_code}")
        return None

# Step 3: Gather Data via NETCONF
def get_netconf_data():
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
        print("Collected Data via NETCONF:\n")
        print(netconf_response.xml)
        return netconf_response.xml

# Step 4: Parse Running Config to Structured Data
def parse_running_config(running_config):
    interfaces = []
    interface_pattern = re.compile(r'interface (?P<name>\S+)\n( (?P<attributes>.*?))?!', re.DOTALL)
    for match in interface_pattern.finditer(running_config):
        interface_name = match.group("name")
        attributes = match.group("attributes")
        interface_data = {"name": interface_name, "attributes": {}}
        if attributes:
            for line in attributes.splitlines():
                line = line.strip()
                if line:
                    key_value = line.split(maxsplit=1)
                    if len(key_value) == 2:
                        key, value = key_value
                        interface_data["attributes"][key] = value
                    else:
                        interface_data["attributes"][key_value[0]] = None
        interfaces.append(interface_data)
    return {"interfaces": interfaces}

# Step 5: Create or Update Data in Nautobot
def create_or_update_in_nautobot(endpoint, data):
    print(f"Creating or updating {endpoint} in Nautobot...")
    nautobot_url = f"http://localhost:8081/api/{endpoint}/"
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
        elif response.status_code == 400 and "already exists" in response.text:
            print(f"{endpoint.capitalize()} already exists. Skipping creation.")
        else:
            print(f"Failed to create or update {endpoint} in Nautobot. Status code: {response.status_code}")
            print(response.text)
    except requests.exceptions.RequestException as e:
        print(f"An error occurred: {e}")

# Step 6: Push Data to Nautobot
def push_to_nautobot(data):
    print("Pushing data to Nautobot...")
    nautobot_url = "http://localhost:8081/api/dcim/devices/"
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
        elif response.status_code == 403:
            print("Failed to push data to Nautobot. Status code: 403 - Forbidden")
            print("Please check your API token and permissions.")
        elif response.status_code == 401:
            print("Failed to push data to Nautobot. Status code: 401 - Unauthorized")
            print("Please ensure your API token is correct.")
        elif response.status_code == 400 and "already exists" in response.text:
            print("Device already exists. Updating existing device...")
            device_id = get_device_id(data["name"])
            if device_id:
                patch_url = f"{nautobot_url}{device_id}/"
                patch_response = requests.patch(patch_url, headers=headers, json=data)
                if patch_response.status_code in [200, 204]:
                    print("Data successfully updated in Nautobot using PATCH.")
                else:
                    print(f"Failed to update data in Nautobot using PATCH. Status code: {patch_response.status_code}")
                    print(patch_response.text)
            else:
                print("Failed to retrieve device ID for updating.")
        elif response.status_code == 400:
            print("Failed to push data to Nautobot. Status code: 400 - Bad Request")
            print("Response from Nautobot:\n")
            print(response.text)
        else:
            print(f"Failed to push data to Nautobot. Status code: {response.status_code}")
            print("Response from Nautobot:\n")
            print(response.text)
    except requests.exceptions.RequestException as e:
        print(f"An error occurred: {e}")

# Helper function to get device ID by name
def get_device_id(device_name):
    print(f"Retrieving device ID for {device_name}...")
    nautobot_url = f"http://localhost:8081/api/dcim/devices/?name={device_name}"
    headers = {
        "Authorization": "Token a2e22503d99e9337ed1e18fdcf8aeb498c224b3f",
    }
    try:
        response = requests.get(nautobot_url, headers=headers)
        if response.status_code == 200:
            results = response.json().get("results", [])
            if results:
                return results[0].get("id")
            else:
                print("Device not found.")
                return None
        else:
            print(f"Failed to retrieve device ID. Status code: {response.status_code}")
            return None
    except requests.exceptions.RequestException as e:
        print(f"An error occurred: {e}")
        return None

if __name__ == "__main__":
    # Choose the method to gather data: 'cli', 'restconf', or 'netconf'
    method = 'cli'  # Change this line to 'restconf' or 'netconf' as needed

    # Gather data based on the chosen method
    if method == 'cli':
        gathered_data = get_running_config()
        device_name = "wee01-leaf-01"
        parsed_data = parse_running_config(gathered_data)
        print(gathered_data)
    elif method == 'restconf':
        gathered_data = get_restconf_data()
        device_name = "wee01-leaf-02"
        parsed_data = gathered_data  # Assuming RESTCONF data is already structured
    elif method == 'netconf':
        gathered_data = get_netconf_data()
        device_name = "wee01-leaf-03"
        parsed_data = gathered_data  # Assuming NETCONF data is already structured
    else:
        raise ValueError("Invalid method chosen. Please select 'cli', 'restconf', or 'netconf'.")

    # Format data to push to Nautobot (this is just an example, adapt as needed)
    nautobot_data = {
        "name": device_name,
        "device_type": {"model": "ASR-9001"},  # Update with an existing model in Nautobot
        "manufacturer": "Cisco",  # Manufacturer name must match what exists in Nautobot
        "role": {"name": "Router"},  # Must match an existing role in Nautobot
        "location": {"name": "Weehawken"},  # Must match an existing site in Nautobot
        "status": {"name": "active"},
        "serial": "123456",  # Example serial number, you can adapt as needed
        "local_config_context_data": {"interfaces": parsed_data["interfaces"]},  # Adding structured config data to config_context
    }

    # Push the gathered data to Nautobot
    push_to_nautobot(nautobot_data)

# Version: 1.0.26
