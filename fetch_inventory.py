import boto3
import argparse
import sys
from botocore.exceptions import ClientError

def parse_arguments():
    """Parse command-line arguments."""
    parser = argparse.ArgumentParser(description='Fetch inventory details from a CloudFormation stack.')
    parser.add_argument('--stack-arn', required=True, help='ARN of the CloudFormation stack')
    return parser.parse_args()

def get_stack_resources(cf_client, stack_arn):
    """Retrieve resources from the CloudFormation stack."""
    try:
        response = cf_client.describe_stack_resources(StackName=stack_arn)
        return response['StackResources']
    except ClientError as e:
        print(f"Error retrieving stack resources: {e}")
        sys.exit(1)

def get_ec2_details(ec2_client, instance_id):
    """Fetch details for an EC2 instance."""
    try:
        response = ec2_client.describe_instances(InstanceIds=[instance_id])
        instance = response['Reservations'][0]['Instances'][0]
        return {
            'InstanceId': instance['InstanceId'],
            'State': instance['State']['Name'],
            'InstanceType': instance['InstanceType'],
            'PublicIp': instance.get('PublicIpAddress', 'N/A')
        }
    except ClientError as e:
        print(f"Error fetching EC2 details for {instance_id}: {e}")
        return None

def get_s3_details(s3_client, bucket_name):
    """Fetch details for an S3 bucket."""
    try:
        response = s3_client.get_bucket_location(Bucket=bucket_name)
        location = response['LocationConstraint'] or 'us-east-1'
        return {
            'BucketName': bucket_name,
            'Region': location
        }
    except ClientError as e:
        print(f"Error fetching S3 details for {bucket_name}: {e}")
        return None

def main():
    """Main function to fetch and display inventory details."""
    args = parse_arguments()
    stack_arn = args.stack_arn

    # Specify region
    region = 'ap-south-1'

    # Initialize boto3 clients with region
    cf_client = boto3.client('cloudformation', region_name=region)
    ec2_client = boto3.client('ec2', region_name=region)
    s3_client = boto3.client('s3', region_name=region)

    # Get stack resources
    resources = get_stack_resources(cf_client, stack_arn)
    inventory = {
        'EC2Instances': [],
        'S3Buckets': []
    }

    # Process each resource
    for resource in resources:
        resource_type = resource['ResourceType']
        physical_id = resource['PhysicalResourceId']
        if resource_type == 'AWS::EC2::Instance':
            details = get_ec2_details(ec2_client, physical_id)
            if details:
                inventory['EC2Instances'].append(details)
        elif resource_type == 'AWS::S3::Bucket':
            details = get_s3_details(s3_client, physical_id)
            if details:
                inventory['S3Buckets'].append(details)

    # Print inventory
    print("\nInventory Details:")
    print("==================")
    if inventory['EC2Instances']:
        print("\nEC2 Instances:")
        for instance in inventory['EC2Instances']:
            print(f"- Instance ID: {instance['InstanceId']}")
            print(f"  State: {instance['State']}")
            print(f"  Instance Type: {instance['InstanceType']}")
            print(f"  Public IP: {instance['PublicIp']}")
    if inventory['S3Buckets']:
        print("\nS3 Buckets:")
        for bucket in inventory['S3Buckets']:
            print(f"- Bucket Name: {bucket['BucketName']}")
            print(f"  Region: {bucket['Region']}")
    if not (inventory['EC2Instances'] or inventory['S3Buckets']):
        print("No resources found in the stack.")

if __name__ == '__main__':
    main()
    