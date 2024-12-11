import re

def parse_interfaces(running_config):
    """
    Parses the interface details from the running configuration.
    """
    interfaces = {}
    current_interface = None

    for line in running_config.splitlines():
        line = line.strip()
        if line.startswith("interface "):
            current_interface = line.split(" ")[1]
            interfaces[current_interface] = {
                "description": "",
                "ipv4_address": None,
                "shutdown": False
            }
        elif current_interface:
            if line.startswith("description"):
                interfaces[current_interface]["description"] = line.split(" ", 1)[1]
            elif line.startswith("ip address"):
                interfaces[current_interface]["ipv4_address"] = line.split(" ")[2]
            elif line == "shutdown":
                interfaces[current_interface]["shutdown"] = True

    return interfaces

def parse_running_config(running_config):
    """
    Parses the running configuration and extracts interface information.
    """
    parsed_data = {
        "interfaces": parse_interfaces(running_config)
    }
    return parsed_data

def parse_vlans(config):
    vlan_data = {}
    vlan_regex = re.compile(r'^vlan (?P<vlan_id>\d+)(?: name (?P<name>\S+))?', re.MULTILINE)
    
    for match in vlan_regex.finditer(config):
        vlan_id = match.group('vlan_id')
        vlan_name = match.group('name') if match.group('name') else f"VLAN_{vlan_id}"
        vlan_data[vlan_id] = {
            "name": vlan_name,
            "vlan_id": vlan_id
        }
    print("Parsed VLAN Data:", parsed_data.get("vlans"))
    return vlan_data