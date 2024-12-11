import requests
import json
from netmiko import ConnectHandler
from parser_utils import parse_interfaces, parse_running_config
from data_collection_utils import get_running_config, get_restconf_data, get_netconf_data
from nautobot_api_utils import create_or_update_in_nautobot, push_to_nautobot, get_device_id
from interface_utils import push_interfaces_to_nautobot, push_vlans_to_nautobot

# Device details for Cisco IOS-XR device
device = {
    "device_type": "cisco_ios",
    "host": "sbx-nxos-mgmt.cisco.com",
    "username": "admin",
    "password": "Admin_1234!",
}

token = "79c056180ba76e6e39b8cccf4b2ef9e635b15c15"

nautobot_url = "http://localhost:8081"  # Update with your Nautobot instance URL


def update_device_config(device_name, running_config, token, nautobot_url):
    """
    Update the Config Context (local_context_data) for a device in Nautobot.

    Args:
        device_name (str): The name of the device in Nautobot.
        running_config (str): The running configuration to store.
        token (str): Nautobot API token.
        nautobot_url (str): Base URL of Nautobot API.

    Returns:
        bool: True if the update was successful, False otherwise.
    """
    # Get the device ID from Nautobot
    device_id = get_device_id(device_name, token)
    if not device_id:
        print(f"Device '{device_name}' not found in Nautobot.")
        return False

    # API endpoint for the specific device
    url = f"{nautobot_url}/dcim/devices/{device_id}/"
    headers = {
        "Authorization": f"Token {token}",
        "Content-Type": "application/json",
    }
    print(f"Headers being sent: {headers}")
    # Prepare the payload to update local_context_data
    payload = {
        "local_config_context_data": {
            "running_config": running_config
        }
    }

    # Send the PATCH request to update the config context
#    response = requests.patch(url, headers=headers, json=payload)

    response = requests.patch(
        f"{nautobot_url}/api/dcim/devices/{device_id}/",
        headers=headers,
        data=json.dumps(payload),
    )
    print(f"API URL: {nautobot_url}/api/dcim/devices/{device_id}/")

    if response.status_code == 200:
        print(f"Successfully updated Config Context for device: {device_name}")
        return True
    else:
        print(f"Failed to update Config Context: {response.status_code} - {response.text}")
        return False




if __name__ == "__main__":
    # Choose the method to gather data: 'cli', 'restconf', or 'netconf'
    method = 'cli'  # Change this line to 'restconf' or 'netconf' as needed

    # Gather data based on the chosen method
    if method == 'cli':
        gathered_data = get_running_config(device)
        parsed_data = parse_running_config(gathered_data)
        device_name = "wee01-leaf-01"  # Ensure the name follows the defined naming standard
    elif method == 'restconf':
        gathered_data = get_restconf_data(device)
        parsed_data = gathered_data
        device_name = "wee01-leaf-01"
    elif method == 'netconf':
        gathered_data = get_netconf_data(device)
        parsed_data = gathered_data
        device_name = "wee01-leaf-01"
    else:
        raise ValueError("Invalid method chosen. Please select 'cli', 'restconf', or 'netconf'.")

    # Format data to push to Nautobot (this is just an example, adapt as needed)
    nautobot_data = {
        "name": device_name,
        "device_type": {"model": "Nexus-9Kv"},  # Update with an existing model in Nautobot
        "manufacturer": "Cisco",  # Manufacturer name must match what exists in Nautobot
        "role": {"name": "Router"},  # Must match an existing role in Nautobot
        "location": {"name": "Weehawken"},  # Must match an existing site in Nautobot
        "status": {"name": "active"},
        "serial": "123456",  # Example serial number, you can adapt as needed
    }

    # Push the gathered data to Nautobot
    push_to_nautobot(nautobot_data, token)

    # Push interface data to Nautobot
    if parsed_data and "interfaces" in parsed_data:
        device_id = get_device_id(device_name, token)
        if device_id:
            push_interfaces_to_nautobot(device_id, parsed_data["interfaces"], token)
        else:
            print("Device ID not found, unable to push interface data.")

    # Push VLAN data to Nautobot
    if parsed_data and "vlans" in parsed_data:
        device_id = get_device_id(device_name, token)
        if device_id:
            push_vlans_to_nautobot(device_id, parsed_data["vlans"], token=token)
        else:
            print("Device ID not found, unable to push VLAN data.")

    # Push configuration data to the Configuration tab
    if gathered_data:

        config_updated = update_device_config(
            nautobot_url=nautobot_url,
            token=token,
            device_name=device_name,
            running_config=gathered_data,
        )
        if not config_updated:
            print(f"Failed to update configuration for device {device_name}.")
