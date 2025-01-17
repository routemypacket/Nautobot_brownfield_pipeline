import os
import requests
import json
from subprocess import run, CalledProcessError
from netmiko import ConnectHandler
from parser_utils import parse_interfaces, parse_running_config
from data_collection_utils import get_running_config, get_restconf_data, get_netconf_data
from nautobot_api_utils import create_or_update_in_nautobot, push_to_nautobot, get_device_id
from interface_utils import push_interfaces_to_nautobot, push_vlans_to_nautobot

# Define the list of devices
devices = [
    {
        "device_type": "cisco_ios",
        "host": "192.168.0.220",
        "username": "cisco",
        "password": "cisco",
        "name": "R1",
    },
    {
        "device_type": "cisco_ios",
        "host": "192.168.0.221",
        "username": "cisco",
        "password": "cisco",
        "name": "R2",
    },
]

# Constants
token = "0123456789abcdef0123456789abcdef01234567"
nautobot_url = "http://192.168.0.44:8001"
git_repo_path = "/mnt/backup"
git_remote_url = "git@github.com:routemypacket/Nautobot_device_backups.git"
commit_message_prefix = "Backup update"


def save_config_to_git(device_name, manufacturer, model, running_config):
    """
    Save the device configuration to a structured directory and push to a Git repository.

    Args:
        device_name (str): Name of the device.
        manufacturer (str): Manufacturer name (e.g., 'Cisco').
        model (str): Device model (e.g., '3725').
        running_config (str): The configuration to save.
    """
    folder_path = os.path.join(git_repo_path, manufacturer, model)
    file_path = os.path.join(folder_path, f"{device_name}.txt")

    # Ensure the folder exists
    os.makedirs(folder_path, exist_ok=True)

    # Write the configuration to the file
    with open(file_path, "w") as config_file:
        config_file.write(running_config)
    print(f"Configuration for {device_name} saved to {file_path}.")

    # Git add, commit, and push
    try:
        run(["git", "-C", git_repo_path, "add", file_path], check=True)
        run(["git", "-C", git_repo_path, "commit", "-m", f"{commit_message_prefix} for {device_name}"], check=True)
        run(["git", "-C", git_repo_path, "push"], check=True)
        print(f"Configuration for {device_name} pushed to Git repository.")
    except CalledProcessError as e:
        print(f"Git operation failed: {e}")


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
    device_id = get_device_id(device_name, token)
    if not device_id:
        print(f"Device '{device_name}' not found in Nautobot.")
        return False

    headers = {
        "Authorization": f"Token {token}",
        "Content-Type": "application/json",
    }
    payload = {
        "local_config_context_data": {
            "running_config": running_config
        }
    }

    response = requests.patch(
        f"{nautobot_url}/api/dcim/devices/{device_id}/",
        headers=headers,
        data=json.dumps(payload),
    )
    if response.status_code == 200:
        print(f"Successfully updated Config Context for device: {device_name}")
        return True
    else:
        print(f"Failed to update Config Context: {response.status_code} - {response.text}")
        return False


if __name__ == "__main__":
    for device in devices:
        device_name = device["name"]
        print(f"Processing device: {device_name}")

        # Use CLI as the default method
        method = 'cli'

        # Gather data based on the chosen method
        if method == 'cli':
            gathered_data = get_running_config(device)
            parsed_data = parse_running_config(gathered_data)
        elif method == 'restconf':
            gathered_data = get_restconf_data(device)
            parsed_data = gathered_data
        elif method == 'netconf':
            gathered_data = get_netconf_data(device)
            parsed_data = gathered_data
        else:
            print(f"Invalid method for device {device_name}. Skipping...")
            continue

        nautobot_data = {
            "name": device_name,
            "device_type": {"model": "3725"},
            "manufacturer": "Cisco",
            "role": {"name": "Border Router"},
            "location": {"name": "ABC"},
            "status": {"name": "Active"},
            "serial": "123456",
        }

        # Push data to Nautobot
        push_to_nautobot(nautobot_data, token)

        # Push configuration data to Git
        if gathered_data:
            save_config_to_git(
                device_name=device_name,
                manufacturer=nautobot_data["manufacturer"],
                model=nautobot_data["device_type"]["model"],
                running_config=gathered_data,
            )

        # Update configuration in Nautobot
        if gathered_data:
            config_updated = update_device_config(
                nautobot_url=nautobot_url,
                token=token,
                device_name=device_name,
                running_config=gathered_data,
            )
            if not config_updated:
                print(f"Failed to update configuration for device {device_name}.")
