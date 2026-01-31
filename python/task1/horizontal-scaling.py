from datetime import datetime, timezone
import boto3
import botocore
import requests
import time
import json
import configparser
import re
from dateutil.parser import parse


########################################
# Constants
########################################
with open('horizontal-scaling-config.json') as file:
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

    # TODO: Create an EC2 instance
    # Wait for the instance to enter the running state
    # Reload the instance attributes

    ec2 = boto3.resource('ec2', region_name='us-east-1')
    
    # This is to launch the instance
    # Note: I must use the TAGS constant that are defined at the top of the file
    instance = ec2.create_instances(
        ImageId=ami,
        InstanceType=INSTANCE_TYPE,
        MinCount=1,
        MaxCount=1,
        SecurityGroupIds=[sg_id],
        TagSpecifications=[{
            'ResourceType': 'instance',
            'Tags': TAGS
        }]
    )[0] # create_instances returns a list, and then I take the first one

    print(f"Instance {instance.id} launching... waiting for running state.")
    
    # To wait for the instance to be running (so that I can get the Public DNS)
    instance.wait_until_running()
    
    # This reloads the instance to fetch the new attributes (like Public DNS)
    instance.reload()
    
    return instance


def initialize_test(lg_dns, first_web_service_dns):
    """
    Start the horizontal scaling test
    :param lg_dns: Load Generator DNS
    :param first_web_service_dns: Web service DNS
    :return: Log file name
    """

    add_ws_string = 'http://{}/test/horizontal?dns={}'.format(
        lg_dns, first_web_service_dns
    )
    response = None
    while not response or response.status_code != 200:
        try:
            response = requests.get(add_ws_string)
        except requests.exceptions.ConnectionError:
            time.sleep(1)
            pass 

    # TODO: return log File name
    log_file_name = get_test_id(response)
    return log_file_name


def print_section(msg):
    """
    Print a section separator including given message
    :param msg: message
    :return: None
    """
    print(('#' * 40) + '\n# ' + msg + '\n' + ('#' * 40))


def get_test_id(response):
    """
    Extracts the test id from the server response.
    :param response: the server response.
    :return: the test name (log file name).
    """
    response_text = response.text

    regexpr = re.compile(TEST_NAME_REGEX)

    return regexpr.findall(response_text)[0]


def is_test_complete(lg_dns, log_name):
    """
    Check if the horizontal scaling test has finished
    :param lg_dns: load generator DNS
    :param log_name: name of the log file
    :return: True if Horizontal Scaling test is complete and False otherwise.
    """

    log_string = 'http://{}/log?name={}'.format(lg_dns, log_name)

    # creates a log file for submission and monitoring
    f = open(log_name + ".log", "w")
    log_text = requests.get(log_string).text
    f.write(log_text)
    f.close()

    return '[Test finished]' in log_text


def add_web_service_instance(lg_dns, sg2_id, log_name):
    """
    Launch a new WS (Web Server) instance and add to the test
    :param lg_dns: load generator DNS
    :param sg2_id: id of WS security group
    :param log_name: name of the log file
    """
    ins = create_instance(WEB_SERVICE_AMI, sg2_id)
    print("New WS launched. id={}, dns={}".format(
        ins.instance_id,
        ins.public_dns_name)
    )
    add_req = 'http://{}/test/horizontal/add?dns={}'.format(
        lg_dns,
        ins.public_dns_name
    )
    while True:
        if requests.get(add_req).status_code == 200:
            print("New WS submitted to LG.")
            break
        elif is_test_complete(lg_dns, log_name):
            print("New WS not submitted because test already completed.")
            break


def get_rps(lg_dns, log_name):
    """
    Return the current RPS as a floating point number
    :param lg_dns: LG DNS
    :param log_name: name of log file
    :return: latest RPS value
    """

    log_string = 'http://{}/log?name={}'.format(lg_dns, log_name)
    config = configparser.ConfigParser(strict=False)
    config.read_string(requests.get(log_string).text)
    sections = config.sections()
    sections.reverse()
    rps = 0
    for sec in sections:
        if 'Current rps=' in sec:
            rps = float(sec[len('Current rps='):])
            break
    return rps


def get_test_start_time(lg_dns, log_name):
    """
    Return the test start time in UTC
    :param lg_dns: LG DNS
    :param log_name: name of log file
    :return: datetime object of the start time in UTC
    """
    log_string = 'http://{}/log?name={}'.format(lg_dns, log_name)
    start_time = None
    while start_time is None:
        config = configparser.ConfigParser(strict=False)
        config.read_string(requests.get(log_string).text)
        # By default, options names in a section are converted
        # to lower case by configparser
        start_time = dict(config.items('Test')).get('starttime', None)
    return parse(start_time)



def wait_for_server_health(dns_name):
    """
    The function waits until the server is actually reachable via HTTP.
    """
    print(f"Waiting for {dns_name} to boot web application...")
    url = f"http://{dns_name}"
    retries = 0
    # Wait up to ~80 seconds for the app to start
    while retries < 40: 
        try:
            resp = requests.get(url, timeout=1)
            if resp.status_code == 200:
                print(f"Server {dns_name} is READY!")
                return True
        except requests.exceptions.RequestException:
            pass # Server not up yet, ignore error
        
        time.sleep(2)
        retries += 1
    
    print(f"Server {dns_name} failed to become ready.")
    return False



########################################
# Main routine
########################################
def main():
    # BIG PICTURE TODO: Provision resources to achieve horizontal scalability
    #   - Create security groups for Load Generator and Web Service
    #   - Provision a Load Generator instance
    #   - Provision a Web Service instance
    #   - Register Web Service DNS with Load Generator
    #   - Add Web Service instances to Load Generator
    #   - Terminate resources

    ec2 = boto3.resource('ec2', region_name='us-east-1')
    ec2_client = boto3.client('ec2', region_name='us-east-1')
    
    # This is the list to track all created instances for cleanup
    all_instance_ids = []

    try:
        # ---------------------------------------------------------
        # 1. Create Security Groups
        # ---------------------------------------------------------
        print_section('1 - create two security groups')
        
        # I can use the same SG for both for simplicity, or create two. 
        # I will create one common SG for this project.
        sg_name = f"vm_scaling_project_sg_{int(time.time())}"
        sg = ec2.create_security_group(
            GroupName=sg_name,
            Description='Security Group for VM Scaling Project'
        )
        
        # Allow SSH (22) and HTTP (80)
        sg.authorize_ingress(
            IpProtocol='tcp', FromPort=80, ToPort=80, CidrIp='0.0.0.0/0'
        )
        # (Optional) Allow SSH if I needed to debug, but not required for the test logic
        # sg.authorize_ingress(IpProtocol='tcp', FromPort=22, ToPort=22, CidrIp='0.0.0.0/0')
        
        sg1_id = sg.id
        sg2_id = sg.id
        print(f"Created Security Group: {sg1_id}")

        # ---------------------------------------------------------
        # 2. Launch Initial Instances (LG and WS)
        # ---------------------------------------------------------
        print_section('2 - create LG')
        
        # Launch Load Generator
        lg_instance = create_instance(LOAD_GENERATOR_AMI, sg1_id)
        all_instance_ids.append(lg_instance.id)
        lg_dns = lg_instance.public_dns_name
        print(f"Load Generator running: id={lg_instance.id} dns={lg_dns}")

        # Launch First Web Service
        ws_instance = create_instance(WEB_SERVICE_AMI, sg2_id)
        all_instance_ids.append(ws_instance.id)
        web_service_dns = ws_instance.public_dns_name
        print(f"First Web Service running: id={ws_instance.id} dns={web_service_dns}")

        
        # ---------------------------------------------------------
        # 3. Start Test & Control Loop
        # ---------------------------------------------------------
        print_section('3. Submit the first WS instance DNS to LG, starting test.')
        
        log_name = initialize_test(lg_dns, web_service_dns)
        print(f"Test Initialized. Log file: {log_name}")

        # Set timer to now so the program starts the first cooldown immediately
        last_launch_time = datetime.now(timezone.utc)

        # RULE 8: Loop strictly based on is_test_complete
        while not is_test_complete(lg_dns, log_name):
            
            # Fetch metrics
            current_rps = get_rps(lg_dns, log_name)
            current_time = datetime.now(timezone.utc)
            time_diff = (current_time - last_launch_time).total_seconds()
            
            print(f"RPS: {current_rps} | Time since last launch: {time_diff:.2f}s")

            # SCALING LOGIC
            # RULE 4: Dynamic check (RPS < 50) and Cooldown (> 100s)
            if current_rps < 50 and time_diff > 100:
                print("RPS is low. Attempting to launch new WS...")
                
                try:
                    # RULE 2 & 4: Launch instance dynamically (No hardcoded limit)
                    # If the program hits the 16 vCPU limit, the 'except' block below catches it.
                    new_ws = create_instance(WEB_SERVICE_AMI, sg2_id)
                    all_instance_ids.append(new_ws.id)
                    
                    # This is to reload to ensure that the program has the Public DNS
                    new_ws.reload()
                    new_ws_dns = new_ws.public_dns_name
                    
                    if not new_ws_dns:
                        print("Error: Instance has no DNS name yet.")
                        # If failed, the program loops again; next iter will retry or wait
                        continue

                    if wait_for_server_health(new_ws_dns):
                        # This adds to Load Generator
                        add_url = f'http://{lg_dns}/test/horizontal/add?dns={new_ws_dns}'
                        res = requests.get(add_url)
                        
                        if res.status_code == 200:
                            # This resets the cooldown only after a successful addition
                            last_launch_time = datetime.now(timezone.utc)
                            print(f"New WS {new_ws.id} successfully added.")
                        else:
                            print(f"Error adding to LG: {res.status_code}")
                    else:
                        print("Skipping add: Server failed health check.")

                except Exception as e:
                    print(f"Scaling paused (likely AWS limit or error): {e}")
            
            # RULE 4: Sleep must be <= 1 second for polling
            time.sleep(1)

        # print_section('Test Finished')

    finally:
        # ---------------------------------------------------------
        # 4. Terminate Resources )
        # ---------------------------------------------------------
        print_section('Cleanup: Terminating Resources')
        if all_instance_ids:
            ec2.instances.filter(InstanceIds=all_instance_ids).terminate()
            print(f"Terminated instances: {all_instance_ids}")
        
        # Cleanup Security Group (wait for instances to terminate first)
        if 'sg' in locals():
            print("Waiting for instances to terminate before deleting SG...")
            # A simple wait loop for SG deletion
            time.sleep(60) 
            try:
                sg.delete()
                print("Security Group deleted.")
            except Exception as e:
                print(f"Could not delete SG (usually because instances are still terminating): {e}")


if __name__ == '__main__':
    main()
