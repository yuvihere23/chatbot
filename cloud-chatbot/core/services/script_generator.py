import logging
import re
from typing import Dict
from datetime import datetime, timedelta

from fastapi import logger
from ..models.query import QueryRequest

# In your script_generator.py
class ScriptGenerator:
    def generate_aws_script(self, query: QueryRequest) -> str:
        """
        Generates AWS script with proper error handling
        """
        try:
            query_lower = query.text.lower()
            
            if any(term in query_lower for term in ['cpu', 'utilization']):
                return self._generate_cpu_script(query)
            elif any(term in query_lower for term in ['cost', 'price']):
                return self._generate_cost_script(query)
            elif any(term in query_lower for term in ['list', 'show']):
                return self._generate_basic_listing_script(query)
            else:
                raise ValueError(f"Unsupported query type: {query.text}")
                
        except Exception as e:
            logger.error(f"Script generation failed: {str(e)}")
            raise  # Re-raise to be handled by the API endpoint

    def _generate_basic_listing_script(self, query: QueryRequest) -> str:
        """
        Generates script for basic instance listing with optional filters
        """
        filters = self._extract_filters(query.text)
        
        return f"""import boto3
import json

def list_instances():
    ec2 = boto3.client('ec2')
    
    filters = {filters}
    response = ec2.describe_instances(Filters=filters)
    
    instances = []
    for reservation in response['Reservations']:
        for instance in reservation['Instances']:
            tags = {{t['Key']: t['Value'] for t in instance.get('Tags', [])}}
            instances.append({{
                'id': instance['InstanceId'],
                'name': tags.get('Name', ''),
                'state': instance['State']['Name'],
                'type': instance.get('InstanceType'),
                'vpc_id': instance.get('VpcId'),
                'subnet_id': instance.get('SubnetId'),
                'private_ip': instance.get('PrivateIpAddress'),
                'public_ip': instance.get('PublicIpAddress'),
                'launch_time': str(instance.get('LaunchTime'))
            }})
    
    return instances

if __name__ == '__main__':
    print(json.dumps(list_instances()))
"""

    def _generate_cpu_script(self, query: QueryRequest) -> str:
        """
        Generates script for CPU-related queries
        """
        threshold = self._extract_threshold(query.text)
        period = self._extract_time_period(query.text)
        
        return f"""import boto3
import json
from datetime import datetime, timedelta

def get_cpu_metrics():
    ec2 = boto3.client('ec2')
    cloudwatch = boto3.client('cloudwatch')
    
    # Get instances based on query filters
    filters = {self._extract_filters(query.text)}
    instances = ec2.describe_instances(Filters=filters)
    
    results = []
    end = datetime.utcnow()
    start = end - timedelta(hours={period})
    
    for reservation in instances['Reservations']:
        for instance in reservation['Instances']:
            # Get CPU metrics
            stats = cloudwatch.get_metric_statistics(
                Namespace='AWS/EC2',
                MetricName='CPUUtilization',
                Dimensions=[{{'Name': 'InstanceId', 'Value': instance['InstanceId']}}],
                StartTime=start,
                EndTime=end,
                Period=3600,
                Statistics=['Average']
            )
            
            avg_cpu = sum(d['Average'] for d in stats['Datapoints'])/len(stats['Datapoints']) if stats['Datapoints'] else 0
            
            if avg_cpu < {threshold}:
                tags = {{t['Key']: t['Value'] for t in instance.get('Tags', [])}}
                results.append({{
                    'id': instance['InstanceId'],
                    'name': tags.get('Name', ''),
                    'cpu_utilization': avg_cpu,
                    'vpc_id': instance.get('VpcId'),
                    'subnet_id': instance.get('SubnetId'),
                    'state': instance['State']['Name'],
                    'period_hours': {period}
                }})
    
    return results

if __name__ == '__main__':
    print(json.dumps(get_cpu_metrics()))
"""

    def _generate_disk_script(self, query: QueryRequest) -> str:
        """
        Generates script for disk/storage related queries
        """
        size_gb = self._extract_size_threshold(query.text)
        
        return f"""import boto3
import json

def get_disk_info():
    ec2 = boto3.client('ec2')
    
    filters = {self._extract_filters(query.text)}
    instances = ec2.describe_instances(Filters=filters)
    
    results = []
    for reservation in instances['Reservations']:
        for instance in reservation['Instances']:
            # Get volume information
            volumes = ec2.describe_volumes(Filters=[
                {{'Name': 'attachment.instance-id', 'Values': [instance['InstanceId']}}
            ])
            
            total_size = sum(v['Size'] for v in volumes['Volumes'])
            if total_size > {size_gb}:
                tags = {{t['Key']: t['Value'] for t in instance.get('Tags', [])}}
                results.append({{
                    'id': instance['InstanceId'],
                    'name': tags.get('Name', ''),
                    'total_disk_gb': total_size,
                    'volumes': [v['VolumeId'] for v in volumes['Volumes']],
                    'vpc_id': instance.get('VpcId'),
                    'subnet_id': instance.get('SubnetId')
                }})
    
    return results

if __name__ == '__main__':
    print(json.dumps(get_disk_info()))
"""

    def _generate_cost_script(self, query: QueryRequest) -> str:
        """
        Final fixed version that handles all edge cases
        """
        filters = self._extract_filters(query.text)
        query_text = query.text.lower().replace('"', '\\"')
        
        script = f"""import boto3
import json
import sys
from datetime import datetime, timedelta

# Fallback pricing for common instance types
FALLBACK_PRICING = {{
    't2.micro': 0.0116,
    't2.small': 0.023,
    't3.micro': 0.0104,
    't3.small': 0.0208
}}

def get_hourly_rate(instance_type):
    try:
        pricing = boto3.client('pricing', region_name='us-east-1')
        response = pricing.get_products(
            ServiceCode='AmazonEC2',
            Filters=[
                {{'Type': 'TERM_MATCH', 'Field': 'instanceType', 'Value': instance_type}},
                {{'Type': 'TERM_MATCH', 'Field': 'operatingSystem', 'Value': 'Linux'}},
                {{'Type': 'TERM_MATCH', 'Field': 'preInstalledSw', 'Value': 'NA'}},
                {{'Type': 'TERM_MATCH', 'Field': 'tenancy', 'Value': 'shared'}}
            ],
            MaxResults=1
        )
        if response['PriceList']:
            price_data = json.loads(response['PriceList'][0])
            price_terms = price_data['terms']['OnDemand']
            price_dimensions = list(price_terms.values())[0]['priceDimensions']
            return float(list(price_dimensions.values())[0]['pricePerUnit']['USD'])
    except Exception:
        return FALLBACK_PRICING.get(instance_type, 0.0)

def get_instance_costs():
    ec2 = boto3.client('ec2')
    now = datetime.utcnow()
    
    # Get running instances
    filters = {filters}
    response = ec2.describe_instances(Filters=filters)
    
    results = []
    for reservation in response['Reservations']:
        for instance in reservation['Instances']:
            launch_time = instance['LaunchTime'].replace(tzinfo=None)
            uptime_hours = (now - launch_time).total_seconds() / 3600
            instance_type = instance['InstanceType']
            hourly_rate = get_hourly_rate(instance_type)
            current_cost = hourly_rate * uptime_hours
            
            results.append({{
                'id': instance['InstanceId'],
                'name': next((t['Value'] for t in instance.get('Tags', []) 
                          if t['Key'] == 'Name'), ''),
                'type': instance_type,
                'hourly_rate': hourly_rate,
                'uptime_hours': round(uptime_hours, 2),
                'current_cost': round(current_cost, 4),
                'launch_time': launch_time.isoformat(),
                'state': instance['State']['Name'],
                'price_source': 'API' if instance_type not in FALLBACK_PRICING else 'Fallback'
            }})
    
    if not results:
        return {{'error': 'No instances found', 'filters': filters}}
    
    # Sort if requested
    if 'expensive' in "{query_text}":
        results.sort(key=lambda x: x['current_cost'], reverse=True)
    elif 'cheap' in "{query_text}":
        results.sort(key=lambda x: x['current_cost'])
    
    return {{
        'report_time': now.isoformat(),
        'instances': results,
        'total_instances': len(results),
        'total_cost': round(sum(i['current_cost'] for i in results), 4),
        'note': 'Costs since instance launch'
    }}

# Generate clean JSON output
try:
    result = get_instance_costs()
    print(json.dumps(result, indent=2))
except Exception as e:
    print(json.dumps({{"error": str(e)}}, indent=2))
"""

        # For debugging - print the generated script to logs
        # import logging
        # logging.basicConfig(level=logging.INFO)
        # logger = logging.getLogger(__name__)
        # logger.info("Generated AWS Cost Script:\n%s", script)
        
        # return script

    def _generate_network_script(self, query: QueryRequest) -> str:
        """
        Generates script for network/VPC/subnet related queries
        """
        return """import boto3
import json

def get_network_info():
    ec2 = boto3.client('ec2')
    
    # Get all instances with network info
    instances = ec2.describe_instances()
    
    # Get all VPCs and subnets for reference
    vpcs = {v['VpcId']: v for v in ec2.describe_vpcs()['Vpcs']}
    subnets = {s['SubnetId']: s for s in ec2.describe_subnets()['Subnets']}
    
    results = []
    for reservation in instances['Reservations']:
        for instance in reservation['Instances']:
            tags = {t['Key']: t['Value'] for t in instance.get('Tags', [])}
            vpc_id = instance.get('VpcId')
            subnet_id = instance.get('SubnetId')
            
            result = {
                'id': instance['InstanceId'],
                'name': tags.get('Name', ''),
                'state': instance['State']['Name'],
                'vpc_id': vpc_id,
                'subnet_id': subnet_id,
                'private_ip': instance.get('PrivateIpAddress'),
                'public_ip': instance.get('PublicIpAddress')
            }
            
            # Add VPC info if available
            if vpc_id in vpcs:
                vpc_tags = {t['Key']: t['Value'] for t in vpcs[vpc_id].get('Tags', [])}
                result.update({
                    'vpc_name': vpc_tags.get('Name', ''),
                    'vpc_cidr': vpcs[vpc_id]['CidrBlock']
                })
            
            # Add subnet info if available
            if subnet_id in subnets:
                subnet_tags = {t['Key']: t['Value'] for t in subnets[subnet_id].get('Tags', [])}
                result.update({
                    'subnet_name': subnet_tags.get('Name', ''),
                    'subnet_cidr': subnets[subnet_id]['CidrBlock'],
                    'availability_zone': subnets[subnet_id]['AvailabilityZone']
                })
            
            results.append(result)
    
    return results

if __name__ == '__main__':
    print(json.dumps(get_network_info()))
"""

    # Helper methods
    def _extract_threshold(self, text: str) -> float:
        """Extracts numerical threshold from query text"""
        try:
            if ">" in text:
                return float(re.search(r'>\s*(\d+)', text).group(1))
            elif "<" in text:
                return float(re.search(r'<\s*(\d+)', text).group(1))
            return 20.0  # Default CPU threshold
        except:
            return 20.0

    def _extract_size_threshold(self, text: str) -> int:
        """Extracts size threshold in GB"""
        try:
            match = re.search(r'(\d+)\s*gb', text.lower())
            return int(match.group(1)) if match else 5
        except:
            return 5

    def _extract_time_period(self, text: str) -> int:
        """Extracts time period in hours"""
        if '24' in text or 'day' in text:
            return 24
        elif 'week' in text:
            return 168
        return 24  # Default to 24 hours

    def _extract_filters(self, text: str) -> list:
        """Extracts EC2 filters from query text"""
        filters = []
        text_lower = text.lower()
        
        # State filters
        if 'running' in text_lower:
            filters.append({'Name': 'instance-state-name', 'Values': ['running']})
        elif 'stopped' in text_lower:
            filters.append({'Name': 'instance-state-name', 'Values': ['stopped']})
        
        # Instance type filters
        if 't2.' in text_lower:
            filters.append({'Name': 'instance-type', 'Values': ['t2.*']})
        elif 't3.' in text_lower:
            filters.append({'Name': 'instance-type', 'Values': ['t3.*']})
        
        # Tag filters
        if 'name=' in text_lower:
            name = re.search(r'name=\s*([^\s]+)', text_lower).group(1)
            filters.append({'Name': 'tag:Name', 'Values': [name]})
        elif 'prod' in text_lower:
            filters.append({'Name': 'tag:Environment', 'Values': ['prod']})
        elif 'dev' in text_lower:
            filters.append({'Name': 'tag:Environment', 'Values': ['dev']})
        
        return filters