import requests
import json

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

def push_to_nautobot(data, token):
    print("Pushing data to Nautobot...")
    nautobot_url = "http://localhost:8000/api/dcim/devices/"
    headers = {
        "Authorization": f"Token {token}",
        "Content-Type": "application/json",
    }
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

def get_device_id(device_name, token):
    print(f"Retrieving device ID for {device_name}...")
    nautobot_url = f"http://localhost:8000/api/dcim/devices/?name={device_name}"
    headers = {
        "Authorization": f"Token {token}",
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