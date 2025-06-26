import logging
from warnings import filters
import boto3
from datetime import datetime, timedelta
from typing import List, Dict, Optional

from fastapi import HTTPException
from .base_adapter import CloudAdapter
from ..models.resource import VirtualMachine, VPC, Subnet, Volume

class AWSAdapter(CloudAdapter):
    def __init__(self, region: str = 'us-east-1'):
        self.region = region
        self.ec2 = boto3.client('ec2', region_name=region)
        self.cloudwatch = boto3.client('cloudwatch', region_name=region)
        
    def list_vms(self, filters: Optional[Dict] = None) -> List[VirtualMachine]:
        try:
            aws_filters = self._convert_filters(filters) if filters else []
            response = self.ec2.describe_instances(Filters=aws_filters)
            
            if not response.get('Reservations'):
                return []  # Return empty list instead of None
                
            return [self._parse_vm(instance) 
                    for reservation in response['Reservations'] 
                    for instance in reservation['Instances']]
        except Exception as e:
            logging.error(f"Error listing VMs: {str(e)}", exc_info=True)
            raise HTTPException(status_code=500, detail=f"AWS API error: {str(e)}")

    def get_vm_details(self, vm_id: str) -> VirtualMachine:
        try:
            response = self.ec2.describe_instances(InstanceIds=[vm_id])
            if not response['Reservations']:
                raise ValueError(f"Instance {vm_id} not found")
            instance = response['Reservations'][0]['Instances'][0]
            return self._parse_vm(instance)
        except Exception as e:
            logging.error(f"Error getting VM details: {str(e)}", exc_info=True)
            raise ValueError(f"Failed to get instance details: {str(e)}")
    
    def list_vpcs(self) -> List[VPC]:
        response = self.ec2.describe_vpcs()
        return [self._parse_vpc(vpc) for vpc in response['Vpcs']]
    
    def list_subnets(self, vpc_id: Optional[str] = None) -> List[Subnet]:
        filters = []
        if vpc_id:
            filters.append({'Name': 'vpc-id', 'Values': [vpc_id]})
        
        response = self.ec2.describe_subnets(Filters=filters)
        return [self._parse_subnet(subnet) for subnet in response['Subnets']]
    
    def get_vm_utilization(self, vm_id: str) -> float:
        end = datetime.utcnow()
        start = end - timedelta(hours=24)  # 24-hour window
        
        response = self.cloudwatch.get_metric_statistics(
            Namespace='AWS/EC2',
            MetricName='CPUUtilization',
            Dimensions=[{'Name': 'InstanceId', 'Value': vm_id}],
            StartTime=start,
            EndTime=end,
            Period=3600,  # 1 hour intervals
            Statistics=['Average']
        )
        
        datapoints = response.get('Datapoints', [])
        if not datapoints:
            return 0.0
        
        # Calculate average CPU over the period
        return sum(point['Average'] for point in datapoints) / len(datapoints)
    
    def get_volumes(self, vm_id: Optional[str] = None) -> List[Volume]:
        filters = []
        if vm_id:
            filters.append({'Name': 'attachment.instance-id', 'Values': [vm_id]})
        
        response = self.ec2.describe_volumes(Filters=filters)
        return [self._parse_volume(vol) for vol in response['Volumes']]
    
    # Helper methods
    def _convert_filters(self, filters: Dict) -> List[Dict]:
        return [{'Name': key, 'Values': [value]} for key, value in filters.items()]
    
    def _parse_vm(self, instance: Dict) -> VirtualMachine:
        tags = {tag['Key']: tag['Value'] for tag in instance.get('Tags', [])}
        return VirtualMachine(
            instance_id=instance['InstanceId'],
            name=tags.get('Name'),
            state=instance['State']['Name'],
            private_ip=instance.get('PrivateIpAddress'),
            public_ip=instance.get('PublicIpAddress'),
            vpc_id=instance.get('VpcId'),
            subnet_id=instance.get('SubnetId'),
            instance_type=instance.get('InstanceType'),
            tags=tags
        )
    
    def _parse_vpc(self, vpc: Dict) -> VPC:
        tags = {tag['Key']: tag['Value'] for tag in vpc.get('Tags', [])}
        return VPC(
            id=vpc['VpcId'],
            name=tags.get('Name'),
            cidr_block=vpc['CidrBlock'],
            region=self.region
        )
    
    def _parse_subnet(self, subnet: Dict) -> Subnet:
        tags = {tag['Key']: tag['Value'] for tag in subnet.get('Tags', [])}
        return Subnet(
            id=subnet['SubnetId'],
            name=tags.get('Name'),
            vpc_id=subnet['VpcId'],
            cidr_block=subnet['CidrBlock'],
            availability_zone=subnet['AvailabilityZone']
        )
    
    def _parse_volume(self, volume: Dict) -> Volume:
        attachments = volume.get('Attachments', [])
        return Volume(
            id=volume['VolumeId'],
            size_gb=volume['Size'],
            volume_type=volume['VolumeType'],
            attached_to=attachments[0]['InstanceId'] if attachments else None,
            encrypted=volume['Encrypted']
        )