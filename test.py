def flatten_json(nested_json, parent_key='', sep='_'):
    items = []
    for k, v in nested_json.items():
        new_key = f"{parent_key}{sep}{k}" if parent_key else k
        if isinstance(v, dict):
            items.extend(flatten_json(v, new_key, sep=sep).items())
        elif isinstance(v, list):
            for i, item in enumerate(v):
                items.extend(flatten_json(item, f"{new_key}{i+1}", sep=sep).items())
        else:
            items.append((new_key, v))
    return dict(items)



test_json = {
    "device_name": "Test Device A",
    "device_type": "cycle",
    "hardware":{
        "sn": "1234",
        "model": "ModelX"
    },
    "software":{
        "version": "1.0.0",
        "last_update": "2024-12-22",
    },
    "software_last_update": "2024-12-22",
    "nic":[
        {
            "type": "Ethernet",
            "mac": "00:1A:2B:3C:4D:5E",
            "ipv4": "192.168.1.1"
        },
        {
            "type": "SIM",
            "mac": "00:1A:2B:3C:4D:5F",
            "ipv4": "192.168.1.2",
        }
    ],
    "dev_description": "A sample device for testing.",
    "password": "testpassword123"
}

my_json = {
    "device_name": "Test Device A",
    "device_type": "cycle",
    "hardware_sn":"1234",
    "hardware_model":"ModelX",
    "software_version": "1.0.0",
    "software_last_update": "2024-12-22",
    "nic1_type": "Ethernet",
    "nic1_mac": "00:1A:2B:3C:4D:5E",
    "nic1_ipv4": "192.168.1.1",
    "nic2_type": "SIM",
    "nic2_mac": "00:1A:2B:3C:4D:5F",
    "nic2_ipv4": "192.168.1.2",
    "dev_description": "A sample device for testing.",
    "password": "testpassword123"
}

print(flatten_json(test_json))
print(flatten_json(test_json) == my_json)