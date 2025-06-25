# app/services/network.py
from azure.mgmt.network import NetworkManagementClient
from app.services.auth import get_credentials, get_subscription_id

def list_vnets():
    client = NetworkManagementClient(get_credentials(), get_subscription_id())
    return [{"name": vnet.name, "id": vnet.id} for vnet in client.virtual_networks.list_all()]

def list_subnets():
    client = NetworkManagementClient(get_credentials(), get_subscription_id())
    subnets_data = []
    for vnet in client.virtual_networks.list_all():
        rg = vnet.id.split("/")[4]
        for subnet in client.subnets.list(rg, vnet.name):
            subnets_data.append({
                "vnet": vnet.name,
                "subnet_name": subnet.name,
                "subnet_id": subnet.id
            })
    return subnets_data
