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


def create_instance(ami, sg_id):
    """
    Given AMI, create and return an AWS EC2 instance object
    :param ami: AMI image name to launch the instance with
    :param sg_id: ID of the security group to be attached to instance
    :return: instance object
    """
    instance = None

    # TODO: Create an EC2 instance

    return instance


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

    # TODO: return log File name
    return ""


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

    # TODO: return log File name
    return ""


def get_test_id(response):
    """
    Extracts the test id from the server response.
    :param response: the server response.
    :return: the test name (log file name).
    """
    response_text = response.text

    regexpr = re.compile(TEST_NAME_REGEX)

    return regexpr.findall(response_text)[0]


def destroy_resources():
    """
    Delete all resources created for this task

    You must destroy the following resources:
    Load Generator, Auto Scaling Group, Launch Template, Load Balancer, Security Group.
    Note that one resource may depend on another, and if resource A depends on resource B, you must delete resource B before you can delete resource A.
    Below are all the resource dependencies that you need to consider in order to decide the correct ordering of resource deletion.

    - You cannot delete Launch Template before deleting the Auto Scaling Group
    - You cannot delete a Security group before deleting the Load Generator and the Auto Scaling Groups
    - You must wait for the instances in your target group to be terminated before deleting the security groups

    :param msg: message
    :return: None
    """
    # TODO: implement this method
    pass


def print_section(msg):
    """
    Print a section separator including given message
    :param msg: message
    :return: None
    """
    print(('#' * 40) + '\n# ' + msg + '\n' + ('#' * 40))


def is_test_complete(load_generator_dns, log_name):
    """
    Check if auto scaling test is complete
    :param load_generator_dns: lg dns
    :param log_name: log file name
    :return: True if Auto Scaling test is complete and False otherwise.
    """
    log_string = 'http://{}/log?name={}'.format(load_generator_dns, log_name)

    # creates a log file for submission and monitoring
    f = open(log_name + ".log", "w")
    log_text = requests.get(log_string).text
    f.write(log_text)
    f.close()

    return '[Test finished]' in log_text


########################################
# Main routine
########################################
def main():
    # BIG PICTURE TODO: Programmatically provision autoscaling resources
    #   - Create security groups for Load Generator and ASG, ELB
    #   - Provision a Load Generator
    #   - Generate a Launch Template
    #   - Create a Target Group
    #   - Provision a Load Balancer
    #   - Associate Target Group with Load Balancer
    #   - Create an Autoscaling Group
    #   - Initialize Warmup Test
    #   - Initialize Autoscaling Test
    #   - Terminate Resources

    print_section('1 - create two security groups')

    PERMISSIONS = [
        {'IpProtocol': 'tcp',
         'FromPort': 80,
         'ToPort': 80,
         'IpRanges': [{'CidrIp': '0.0.0.0/0'}],
         'Ipv6Ranges': [{'CidrIpv6': '::/0'}],
         }
    ]

    # TODO: create two separate security groups and obtain the group ids
    sg1_id = None  # Security group for Load Generator instances
    sg2_id = None  # Security group for ASG, ELB instances

    print_section('2 - create LG')

    # TODO: Create Load Generator instance and obtain ID and DNS
    lg = ''
    lg_id = ''
    lg_dns = ''
    print("Load Generator running: id={} dns={}".format(lg_id, lg_dns))

    print_section('3. Create LT (Launch Template)')
    # TODO: create launch Template

    print_section('4. Create TG (Target Group)')
    # TODO: create Target Group
    tg_arn = ''

    print_section('5. Create ELB (Elastic/Application Load Balancer)')

    # TODO create Load Balancer
    # https://boto3.amazonaws.com/v1/documentation/api/latest/reference/services/elbv2.html
    lb_arn = ''
    lb_dns = ''
    print("lb started. ARN={}, DNS={}".format(lb_arn, lb_dns))

    print_section('6. Associate ELB with target group')
    # TODO Associate ELB with target group

    print_section('7. Create ASG (Auto Scaling Group)')
    # TODO create Autoscaling group

    print_section('8. Create policy and attached to ASG')
    # TODO Create Simple Scaling Policies for ASG

    print_section('9. Create Cloud Watch alarm. Action is to invoke policy.')
    # TODO create CloudWatch Alarms and link Alarms to scaling policies

    print_section('10. Submit ELB DNS to LG, starting warm up test.')
    warmup_log_name = initialize_warmup(lg_dns, lb_dns)
    while not is_test_complete(lg_dns, warmup_log_name):
        time.sleep(1)

    print_section('11. Submit ELB DNS to LG, starting auto scaling test.')
    # May take a few minutes to start actual test after warm up test finishes
    log_name = initialize_test(lg_dns, lb_dns)
    while not is_test_complete(lg_dns, log_name):
        time.sleep(1)

    destroy_resources()


if __name__ == "__main__":
    main()
