from ncclient import manager

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