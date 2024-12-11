import requests

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