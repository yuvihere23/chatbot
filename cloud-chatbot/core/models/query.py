# core/models/query.py
from enum import Enum
from pydantic import BaseModel, Field
from typing import List, Optional, TypeVar, Generic
from core.models.resource import VirtualMachine, VPC, Subnet, Volume

T = TypeVar('T')

class QueryType(str, Enum):
    SIMPLE = "simple"
    COMPLEX = "complex"

class CloudProvider(str, Enum):
    AWS = "aws"
    AZURE = "azure"

class QueryRequest(BaseModel):
    text: str
    cloud: CloudProvider
    filters: dict = Field(default_factory=dict)
    detailed: bool = False  # Add this field

class QueryResponse(BaseModel, Generic[T]):
    success: bool
    data: Optional[T] = Field(default_factory=list)  # Default empty list for collection types
    error: Optional[str] = None
    query_type: QueryType