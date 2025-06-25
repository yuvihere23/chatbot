# app/services/vm_info.py
from azure.mgmt.compute import ComputeManagementClient
from azure.mgmt.network import NetworkManagementClient
from app.services.auth import get_credentials, get_subscription_id

def list_vms():
    cred = get_credentials()
    sub = get_subscription_id()
    compute = ComputeManagementClient(cred, sub)
    network = NetworkManagementClient(cred, sub)
    
    results = []
    for vm in compute.virtual_machines.list_all():
        rg = vm.id.split("/")[4]
        nic_id = vm.network_profile.network_interfaces[0].id
        nic_name = nic_id.split('/')[-1]
        nic = network.network_interfaces.get(rg, nic_name)
        ip = nic.ip_configurations[0].private_ip_address
        subnet_id = nic.ip_configurations[0].subnet.id
        results.append({
            "name": vm.name,
            "resource_group": rg,
            "private_ip": ip,
            "subnet_id": subnet_id,
            "vm_id": vm.id
        })
    return results
