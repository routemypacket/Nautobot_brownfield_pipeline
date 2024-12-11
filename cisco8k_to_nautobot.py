from netmiko import ConnectHandler
import requests
import json

# Cisco switch details
switch = {
    'device_type': 'cisco_ios',
    'host': '10.10.20.48',
    'username': 'developer',
    'password': 'C1sco12345',
}

# Connect to the switch
try:
    net_connect = ConnectHandler(**switch)
    output = net_connect.send_command('show running-config')

    print (output)
    # Close connection
    net_connect.disconnect()

    # Post config data to Nautobot
    nautobot_url = 'http://localhost:8000/api/'
    token = 'dadab498fca1ef6b3e221c2e9b4cc81dc1f3e1f4'
    headers = {
        'Content-Type': 'application/json',
        'Authorization': f'Token {token}',
    }
    data = {
        'name': 'Cisco Switch Configuration',
        'config': output,
        # Add more fields as needed based on Nautobot API requirements
    }
    response = requests.post(f'{nautobot_url}/configurations/', headers=headers, data=json.dumps(data))

    # Check response status
    if response.status_code == 201:
        print('Configuration uploaded successfully to Nautobot.')
    else:
        print(f'Failed to upload configuration to Nautobot. Status code: {response.status_code}')

except Exception as e:
    print(f'Error: {str(e)}')