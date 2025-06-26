from pydantic import BaseModel, Field, validator
from typing import Optional, Dict, List
from enum import Enum

class VMState(str, Enum):
    RUNNING = "running"
    STOPPED = "stopped"
    TERMINATED = "terminated"
    PENDING = "pending"
    STOPPING = "stopping"
    SHUTTING_DOWN = "shutting-down"

class VirtualMachine(BaseModel):
    # Primary field is instance_id, but accepts 'id' as input
    instance_id: str = Field(..., alias="instance_id")
    name: Optional[str] = None
    state: Optional[VMState] = None
    private_ip: Optional[str] = None
    public_ip: Optional[str] = None
    vpc_id: Optional[str] = None
    subnet_id: Optional[str] = None
    instance_type: Optional[str] = None
    cpu_utilization: Optional[float] = Field(None, ge=0, le=100)
    cost: Optional[float] = Field(None, ge=0)
    tags: Optional[Dict[str, str]] = None
    volumes: Optional[List['Volume']] = None

    @validator('instance_id', pre=True)
    def validate_instance_id(cls, v):
        # Handle case where input uses 'id' instead of 'instance_id'
        if isinstance(v, dict) and 'id' in v and 'instance_id' not in v:
            return v['id']
        return v

    class Config:
        # Allows both field names in input
        allow_population_by_field_name = True

class VPC(BaseModel):
    id: str
    name: Optional[str] = None
    cidr_block: Optional[str] = None
    subnets: Optional[List['Subnet']] = None
    region: Optional[str] = None

class Subnet(BaseModel):
    id: str
    name: Optional[str] = None
    vpc_id: Optional[str] = None
    cidr_block: Optional[str] = None
    availability_zone: Optional[str] = None

class Volume(BaseModel):
    id: str
    size_gb: int
    volume_type: str
    attached_to: Optional[str] = None
    encrypted: bool = False
    iops: Optional[int] = None
    throughput: Optional[int] = None

# Update forward references
VirtualMachine.update_forward_refs()
VPC.update_forward_refs()