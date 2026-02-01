import boto3
import botocore
import requests
import time
import json
import re

########################################
# Constants
########################################
with open('auto-scaling-config.json') as file:
    configuration = json.load(file)

LOAD_GENERATOR_AMI = configuration['load_generator_ami']
WEB_SERVICE_AMI = configuration['web_service_ami']
INSTANCE_TYPE = configuration['instance_type']

########################################
# Clients
########################################
ec2 = boto3.client('ec2')
elbv2 = boto3.client('elbv2')
asg_client = boto3.client('autoscaling')
cw_client = boto3.client('cloudwatch')

########################################
# Tags
########################################
tag_pairs = [
    ("Project", "vm-scaling"),
]
TAGS = [{'Key': k, 'Value': v} for k, v in tag_pairs]

TEST_NAME_REGEX = r'name=(.*log)'

########################################
# Utility functions
########################################

def get_default_vpc():
    """A helper function to get the default VPC ID."""
    response = ec2.describe_vpcs(Filters=[{'Name': 'isDefault', 'Values': ['true']}])
    return response['Vpcs'][0]['VpcId']

def get_subnets(vpc_id):
    """A helper function to get all subnets for a VPC."""
    response = ec2.describe_subnets(Filters=[{'Name': 'vpc-id', 'Values': [vpc_id]}])
    return [subnet['SubnetId'] for subnet in response['Subnets']]

def create_instance(ami, sg_id):
    """
    Given AMI, create and return an AWS EC2 instance object
    """
    print(f"Now launching instance with AMI: {ami}...")
    response = ec2.run_instances(
        ImageId=ami,
        InstanceType=INSTANCE_TYPE,
        SecurityGroupIds=[sg_id],
        MinCount=1,
        MaxCount=1,
        TagSpecifications=[{'ResourceType': 'instance', 'Tags': TAGS}]
    )
    instance_id = response['Instances'][0]['InstanceId']
    
    # To wait for the running state
    print(f"Now waiting for the instance {instance_id} to be running...")
    waiter = ec2.get_waiter('instance_running')
    waiter.wait(InstanceIds=[instance_id])
    
    # To reload the instance info to get DNS
    desc = ec2.describe_instances(InstanceIds=[instance_id])
    
    # To access the inside reservations
    return desc['Reservations'][0]['Instances'][0]

def initialize_test(load_generator_dns, first_web_service_dns):
    """

    Start the auto scaling test

    :param lg_dns: Load Generator DNS

    :param first_web_service_dns: Web service DNS

    :return: Log file name

    """

    add_ws_string = 'http://{}/autoscaling?dns={}'.format(
        load_generator_dns, first_web_service_dns
    )
    response = None
    while not response or response.status_code != 200:
        try:
            response = requests.get(add_ws_string)
        except requests.exceptions.ConnectionError:
            time.sleep(1)
            pass 
    # To return the log File name
    return get_test_id(response)

def initialize_warmup(load_generator_dns, load_balancer_dns):
    """

    Start the warmup test

    :param lg_dns: Load Generator DNS

    :param load_balancer_dns: Load Balancer DNS

    :return: Log file name

    """

    add_ws_string = 'http://{}/warmup?dns={}'.format(
        load_generator_dns, load_balancer_dns
    )
    response = None
    while not response or response.status_code != 200:
        try:
            response = requests.get(add_ws_string)
        except requests.exceptions.ConnectionError:
            time.sleep(1)
            pass  
    # To return the log File name
    return get_test_id(response)

def get_test_id(response):
    response_text = response.text
    regexpr = re.compile(TEST_NAME_REGEX)
    return regexpr.findall(response_text)[0]

def destroy_resources():
    """
    Delete all resources created for this task in reverse order.
    """
    print_section('Cleanup: Terminating Resources')
    
    # 1. To delete the ASG
    try:
        print("Now deleting the Auto Scaling Group...")
        asg_client.delete_auto_scaling_group(
            AutoScalingGroupName=configuration['auto_scaling_group_name'],
            ForceDelete=True
        )
        while True:
            try:
                desc = asg_client.describe_auto_scaling_groups(
                    AutoScalingGroupNames=[configuration['auto_scaling_group_name']]
                )
                if not desc['AutoScalingGroups']:
                    break 
                if desc['AutoScalingGroups'][0]['Status'] == 'Delete in progress':
                    print("ASG deletion in progress...")
                    time.sleep(5)
            except:
                break
    except Exception as e:
        print(f"There was an error while deleting ASG: {e}")

    # 2. To delete the Launch template
    try:
        print("Now deleting the launch template...")
        ec2.delete_launch_template(LaunchTemplateName=configuration['launch_template_name'])
    except Exception as e:
        print(f"Error deleting LT: {e}")

    # 3. To delete the Load Balancer
    lb_arn = None
    try:
        lbs = elbv2.describe_load_balancers(Names=[configuration['load_balancer_name']])
        if lbs['LoadBalancers']:
            lb_arn = lbs['LoadBalancers'][0]['LoadBalancerArn']
            print("Deleting Load Balancer...")
            elbv2.delete_load_balancer(LoadBalancerArn=lb_arn)
            
            print("Waiting for LB deletion...")
            waiter = elbv2.get_waiter('load_balancers_deleted')
            waiter.wait(LoadBalancerArns=[lb_arn])
            # To give AWS a moment to release the Target Group lock
            time.sleep(10) 
    except Exception as e:
        print(f"Error deleting LB: {e}")

    # 4. To delete the Target Group
    try:
        tgs = elbv2.describe_target_groups(Names=[configuration['auto_scaling_target_group']])
        if tgs['TargetGroups']:
            tg_arn = tgs['TargetGroups'][0]['TargetGroupArn']
            print("Deleting Target Group...")
            elbv2.delete_target_group(TargetGroupArn=tg_arn)
    except Exception as e:
        print(f"Error deleting TG: {e}")

    # 5. To delete the Load Generator Instance
    try:
        print("Now terminating the Load Generator...")
        instances = ec2.describe_instances(
            Filters=[
                {'Name': 'tag:Project', 'Values': ['vm-scaling']},
                {'Name': 'instance-state-name', 'Values': ['running', 'pending']}
            ]
        )
        ids_to_term = []
        for r in instances['Reservations']:
            for i in r['Instances']:
                ids_to_term.append(i['InstanceId'])
        
        if ids_to_term:
            ec2.terminate_instances(InstanceIds=ids_to_term)
            print(f"Terminating: {ids_to_term}")
            waiter = ec2.get_waiter('instance_terminated')
            waiter.wait(InstanceIds=ids_to_term)
    except Exception as e:
        print(f"Error terminating instances: {e}")

    # 6. To delete the CloudWatch Alarms
    try:
        print("Now deleting the CloudWatch Alarms...")
        cw_client.delete_alarms(AlarmNames=['ScaleOutAlarm', 'ScaleInAlarm'])
    except Exception as e:
        print(f"Error deleting alarms: {e}")


def print_section(msg):
    print(('#' * 40) + '\n# ' + msg + '\n' + ('#' * 40))


def is_test_complete(load_generator_dns, log_name):
    log_string = 'http://{}/log?name={}'.format(load_generator_dns, log_name)
    f = open(log_name + ".log", "w")
    try:
        log_text = requests.get(log_string).text
        f.write(log_text)
    except:
        pass
    f.close()
    
    # To read file to check content
    with open(log_name + ".log", "r") as f:
        content = f.read()
        return '[Test finished]' in content


########################################
# Main routine
########################################
def main():
    try:
        vpc_id = get_default_vpc()
        subnets = get_subnets(vpc_id)
        
        print_section('1 - create two security groups')
        sg_lg_name = f"sg_lg_{int(time.time())}"
        sg1_resp = ec2.create_security_group(GroupName=sg_lg_name, Description="LG SG", VpcId=vpc_id)
        sg1_id = sg1_resp['GroupId']
        ec2.authorize_security_group_ingress(
            GroupId=sg1_id,
            IpPermissions=[{'IpProtocol': 'tcp', 'FromPort': 80, 'ToPort': 80, 'IpRanges': [{'CidrIp': '0.0.0.0/0'}]}]
        )
        ec2.authorize_security_group_ingress(
            GroupId=sg1_id,
            IpPermissions=[{'IpProtocol': 'tcp', 'FromPort': 22, 'ToPort': 22, 'IpRanges': [{'CidrIp': '0.0.0.0/0'}]}]
        )
        print(f"Created LG SG: {sg1_id}")

        sg_web_name = f"sg_web_{int(time.time())}"
        sg2_resp = ec2.create_security_group(GroupName=sg_web_name, Description="Web/ELB SG", VpcId=vpc_id)
        sg2_id = sg2_resp['GroupId']
        ec2.authorize_security_group_ingress(
            GroupId=sg2_id,
            IpPermissions=[{'IpProtocol': 'tcp', 'FromPort': 80, 'ToPort': 80, 'IpRanges': [{'CidrIp': '0.0.0.0/0'}]}]
        )
        print(f"Created Web SG: {sg2_id}")

        print_section('2 - create LG')
        lg_instance = create_instance(LOAD_GENERATOR_AMI, sg1_id)
        lg_id = lg_instance['InstanceId']
        lg_dns = lg_instance['PublicDnsName']
        print("Load Generator running: id={} dns={}".format(lg_id, lg_dns))

        print_section('3. Create LT (Launch Template)')
        lt_name = configuration['launch_template_name']
        ec2.create_launch_template(
            LaunchTemplateName=lt_name,
            LaunchTemplateData={
                'ImageId': WEB_SERVICE_AMI,
                'InstanceType': INSTANCE_TYPE,
                'SecurityGroupIds': [sg2_id],
                'TagSpecifications': [{'ResourceType': 'instance', 'Tags': TAGS}],
                'Monitoring': {'Enabled': True} 
            }
        )
        print(f"Launch Template {lt_name} created.")

        print_section('4. Create TG (Target Group)')
        tg_name = configuration['auto_scaling_target_group']
        tg_resp = elbv2.create_target_group(
            Name=tg_name,
            Protocol='HTTP',
            Port=80,
            VpcId=vpc_id,
            HealthCheckProtocol='HTTP',
            HealthCheckPath='/',
            TargetType='instance'
        )
        tg_arn = tg_resp['TargetGroups'][0]['TargetGroupArn']
        print(f"Target Group created: {tg_arn}")

        print_section('5. Create ELB (Application Load Balancer)')
        lb_name = configuration['load_balancer_name']
        lb_resp = elbv2.create_load_balancer(
            Name=lb_name,
            Subnets=subnets,
            SecurityGroups=[sg2_id],
            Scheme='internet-facing',
            Tags=TAGS,
            Type='application'
        )
        lb_arn = lb_resp['LoadBalancers'][0]['LoadBalancerArn']
        lb_dns = lb_resp['LoadBalancers'][0]['DNSName']
        
        print("Waiting for Load Balancer to be active...")
        lb_waiter = elbv2.get_waiter('load_balancer_available')
        lb_waiter.wait(LoadBalancerArns=[lb_arn])
        print("lb started. ARN={}, DNS={}".format(lb_arn, lb_dns))

        print_section('6. Associate ELB with target group')
        elbv2.create_listener(
            LoadBalancerArn=lb_arn,
            Protocol='HTTP',
            Port=80,
            DefaultActions=[{'Type': 'forward', 'TargetGroupArn': tg_arn}]
        )
        print("Listener created.")

        print_section('7. Create ASG (Auto Scaling Group)')
        asg_name = configuration['auto_scaling_group_name']
        asg_client.create_auto_scaling_group(
            AutoScalingGroupName=asg_name,
            LaunchTemplate={
                'LaunchTemplateName': lt_name,
                'Version': '$Latest'
            },
            MinSize=configuration['asg_min_size'],
            MaxSize=configuration['asg_max_size'],
            DesiredCapacity=1,
            DefaultCooldown=configuration['asg_default_cool_down_period'],
            TargetGroupARNs=[tg_arn],
            VPCZoneIdentifier=",".join(subnets),
            Tags=[{'Key': 'Project', 'Value': 'vm-scaling', 'PropagateAtLaunch': True}],
            HealthCheckType='EC2',
            HealthCheckGracePeriod=configuration['health_check_grace_period']
        )
        print(f"ASG {asg_name} created.")

        print_section('8. Create policy and attached to ASG')
        scale_out_resp = asg_client.put_scaling_policy(
            AutoScalingGroupName=asg_name,
            PolicyName='ScaleOutPolicy',
            PolicyType='SimpleScaling',
            AdjustmentType='ChangeInCapacity',
            ScalingAdjustment=configuration['scale_out_adjustment'],
            Cooldown=configuration['cool_down_period_scale_out']
        )
        scale_out_arn = scale_out_resp['PolicyARN']

        scale_in_resp = asg_client.put_scaling_policy(
            AutoScalingGroupName=asg_name,
            PolicyName='ScaleInPolicy',
            PolicyType='SimpleScaling',
            AdjustmentType='ChangeInCapacity',
            ScalingAdjustment=configuration['scale_in_adjustment'],
            Cooldown=configuration['cool_down_period_scale_in']
        )
        scale_in_arn = scale_in_resp['PolicyARN']
        print("Scaling policies created.")

        print_section('9. Create Cloud Watch alarm.')
        cw_client.put_metric_alarm(
            AlarmName='ScaleOutAlarm',
            MetricName='CPUUtilization',
            Namespace='AWS/EC2',
            Statistic='Average',
            Dimensions=[{'Name': 'AutoScalingGroupName', 'Value': asg_name}],
            Period=configuration['alarm_period'],
            EvaluationPeriods=configuration['alarm_evaluation_periods_scale_out'],
            Threshold=configuration['cpu_upper_threshold'],
            ComparisonOperator='GreaterThanThreshold',
            AlarmActions=[scale_out_arn]
        )
        cw_client.put_metric_alarm(
            AlarmName='ScaleInAlarm',
            MetricName='CPUUtilization',
            Namespace='AWS/EC2',
            Statistic='Average',
            Dimensions=[{'Name': 'AutoScalingGroupName', 'Value': asg_name}],
            Period=configuration['alarm_period'],
            EvaluationPeriods=configuration['alarm_evaluation_periods_scale_in'],
            Threshold=configuration['cpu_lower_threshold'],
            ComparisonOperator='LessThanThreshold',
            AlarmActions=[scale_in_arn]
        )
        print("CloudWatch Alarms created.")

        print_section('10. Submit ELB DNS to LG, starting warm up test.')
        time.sleep(10)
        warmup_log_name = initialize_warmup(lg_dns, lb_dns)
        print(f"Warmup log: {warmup_log_name}")
        while not is_test_complete(lg_dns, warmup_log_name):
            time.sleep(10)

        # -------------------------------------------------------------
        # To RESET ASG TO 1 BEFORE MAIN TEST
        # -------------------------------------------------------------
        print_section('10.5. Reset ASG to 1 instance before main test')
        print("The warmup likely scaled the ASG up. Forcing scale down to 1 to save budget...")
        asg_client.update_auto_scaling_group(
            AutoScalingGroupName=asg_name,
            DesiredCapacity=1
        )
        # To give it 60 seconds to terminate the extra instances
        time.sleep(60)
        # -------------------------------------------------------------

        print_section('11. Submit ELB DNS to LG, starting auto scaling test.')
        log_name = initialize_test(lg_dns, lb_dns)
        print(f"Test log: {log_name}")
        while not is_test_complete(lg_dns, log_name):
            time.sleep(20)

        destroy_resources()
        
    except Exception as e:
        print(f"CRITICAL ERROR: {e}")
        destroy_resources()

if __name__ == "__main__":
    main()