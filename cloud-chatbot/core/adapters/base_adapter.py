from abc import ABC, abstractmethod
from typing import List, Dict, Optional
from ..models.resource import VirtualMachine, VPC, Subnet, Volume

class CloudAdapter(ABC):
    @abstractmethod
    def list_vms(self, filters: Optional[Dict] = None) -> List[VirtualMachine]:
        pass
        
    @abstractmethod
    def get_vm_details(self, vm_id: str) -> VirtualMachine:
        pass
    
    @abstractmethod
    def list_vpcs(self) -> List[VPC]:
        pass
    
    @abstractmethod
    def list_subnets(self, vpc_id: Optional[str] = None) -> List[Subnet]:
        pass
    
    @abstractmethod
    def get_vm_utilization(self, vm_id: str) -> float:
        pass
    
    @abstractmethod
    def get_volumes(self, vm_id: Optional[str] = None) -> List[Volume]:
        pass