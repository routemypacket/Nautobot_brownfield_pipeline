import requests

def push_interfaces_to_nautobot(device_id, interfaces, token):
    print(f"Pushing interface data for device ID {device_id} to Nautobot...")
    nautobot_url = "http://localhost:8000/api/dcim/interfaces/"
    headers = {
        "Authorization": f"Token {token}",
        "Content-Type": "application/json",
    }

    for interface_name, interface_data in interfaces.items():
        # Extract VLAN information from parsed data if available
        untagged_vlan = interface_data.get("untagged_vlan")
        tagged_vlans = interface_data.get("tagged_vlans", [])

        # Prepare the payload to create or update an interface
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
                "id": "3e1a93d4-cef2-4b05-8fb4-838ff0f5efcb"  # Correct UUID for 'active' status
            },
        }

        # Add VLAN details to the interface payload
        if untagged_vlan:
            interface_payload["untagged_vlan"] = {
                "id": untagged_vlan.get("id"),
                "object_type": "ipam.vlan",
                "url": f"http://localhost:8000/api/ipam/vlans/{untagged_vlan.get('id')}/"
            }

        if tagged_vlans:
            interface_payload["tagged_vlans"] = [
                {
                    "id": vlan.get("id"),
                    "object_type": "ipam.vlan",
                    "url": f"http://localhost:8000/api/ipam/vlans/{vlan.get('id')}/"
                }
                for vlan in tagged_vlans
            ]

        # Check if the interface already exists
        try:
            check_url = f"http://localhost:8000/api/dcim/interfaces/?device_id={device_id}&name={interface_name}"
            response = requests.get(check_url, headers=headers)
            if response.status_code == 200 and response.json()["count"] > 0:
                # Interface exists, perform PATCH
                interface_id = response.json()["results"][0]["id"]
                patch_url = f"http://localhost:8000/api/dcim/interfaces/{interface_id}/"
                response = requests.patch(patch_url, headers=headers, json=interface_payload)
                if response.status_code in [200, 204]:
                    print(f"Interface '{interface_name}' successfully updated.")
                else:
                    print(f"Failed to update interface '{interface_name}'. Status code: {response.status_code}")
                    print(response.text)
            else:
                # Interface does not exist, perform POST
                response = requests.post(nautobot_url, headers=headers, json=interface_payload)
                if response.status_code == 201:
                    print(f"Interface '{interface_name}' successfully created.")
                else:
                    print(f"Failed to create interface '{interface_name}'. Status code: {response.status_code}")
                    print(response.text)
        except requests.exceptions.RequestException as e:
            print(f"An error occurred while processing interface '{interface_name}': {e}")

def push_vlans_to_nautobot(device_id, vlans, token):
    print(f"Pushing VLAN data for device ID {device_id} to Nautobot...")
    for vlan_id, vlan_data in vlans.items():
        vlan_payload = {
            "name": vlan_data["name"],
            "vid": vlan_data["vlan_id"],
            "status": "active",
            "device": device_id
        }
        try:
            response = requests.post(
                "http://localhost:8000/api/ipam/vlans/",
                headers={
                    "Authorization": f"Token {token}",
                    "Content-Type": "application/json",
                },
                json=vlan_payload
            )
            if response.status_code == 201:
                print(f"VLAN '{vlan_id}' successfully created.")
            elif response.status_code == 400:
                print(f"Failed to create VLAN '{vlan_id}'. Status code: 400 - Bad Request")
                print("Response from Nautobot:")
                print(response.text)
            else:
                print(f"Failed to create VLAN '{vlan_id}'. Status code: {response.status_code}")
                print(response.text)
        except requests.exceptions.RequestException as e:
            print(f"An error occurred while pushing VLAN data: {e}")
