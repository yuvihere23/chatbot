from fastapi import APIRouter, HTTPException
from typing import Optional, Dict, List, Union
from core.adapters.aws_adapter import AWSAdapter
from core.adapters.azure_adapter import AzureAdapter
from core.models.resource import (VirtualMachine, VPC, Subnet, Volume)
from core.models.query import QueryResponse  # Changed import source

router = APIRouter()

def get_adapter(cloud: str):
    if cloud == "aws":
        return AWSAdapter()
    elif cloud == "azure":
        return AzureAdapter()
    raise HTTPException(status_code=400, detail=f"Unsupported cloud provider: {cloud}")

@router.get("/{cloud}/vms", response_model=QueryResponse)
async def list_vms(
    cloud: str,
    detailed: bool = False,
    state: Optional[str] = None,
    vpc_id: Optional[str] = None
):
    """List all VMs with optional filtering"""
    adapter = get_adapter(cloud)
    filters = {}
    if state:
        filters['instance-state-name'] = state.lower()
    if vpc_id:
        filters['vpc-id'] = vpc_id
    
    vms = adapter.list_vms(filters if filters else None)
    
    if detailed:
        detailed_vms = []
        for vm in vms:
            detailed_vm = adapter.get_vm_details(vm.id)
            detailed_vm.cpu_utilization = adapter.get_vm_utilization(vm.id)
            detailed_vm.volumes = adapter.get_volumes(vm.id)
            detailed_vms.append(detailed_vm)
        return QueryResponse(success=True, data=detailed_vms)
    
    return QueryResponse(success=True, data=vms)

@router.get("/{cloud}/vms/{vm_id}", response_model=QueryResponse)
async def get_vm_details(cloud: str, vm_id: str):
    """Get detailed information about a specific VM"""
    adapter = get_adapter(cloud)
    vm = adapter.get_vm_details(vm_id)
    vm.cpu_utilization = adapter.get_vm_utilization(vm_id)
    vm.volumes = adapter.get_volumes(vm_id)
    return QueryResponse(success=True, data=vm)

@router.get("/{cloud}/vpcs", response_model=QueryResponse)
async def list_vpcs(cloud: str, detailed: bool = False):
    """List all VPCs with optional subnet details"""
    adapter = get_adapter(cloud)
    vpcs = adapter.list_vpcs()
    
    if detailed:
        for vpc in vpcs:
            vpc.subnets = adapter.list_subnets(vpc.id)
    
    return QueryResponse(success=True, data=vpcs)

@router.get("/{cloud}/subnets", response_model=QueryResponse)
async def list_subnets(cloud: str, vpc_id: Optional[str] = None):
    """List all subnets, optionally filtered by VPC"""
    adapter = get_adapter(cloud)
    subnets = adapter.list_subnets(vpc_id)
    return QueryResponse(success=True, data=subnets)

@router.get("/{cloud}/volumes", response_model=QueryResponse)
async def list_volumes(cloud: str, vm_id: Optional[str] = None):
    """List all volumes, optionally filtered by VM"""
    adapter = get_adapter(cloud)
    volumes = adapter.get_volumes(vm_id)
    return QueryResponse(success=True, data=volumes)