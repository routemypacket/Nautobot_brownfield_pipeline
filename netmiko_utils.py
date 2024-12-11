from netmiko import ConnectHandler

def get_running_config(device):
    print("Connecting to device via CLI using Netmiko...")
    connection = ConnectHandler(**device)
    running_config = connection.send_command("show running-config")
    connection.disconnect()
    return running_config