"""Library for common methods that are used by the different configs scripts."""

import sys
import os
import json
import pprint
import time
import getpass
import string
import subprocess
import shlex

import hosts

# Add a reference to boss-manage/vault/ so that we can import those files
cur_dir = os.path.dirname(os.path.realpath(__file__))
vault_dir = os.path.normpath(os.path.join(cur_dir, "..", "vault"))
sys.path.append(vault_dir)
import bastion
import vault

def get_commit():
    try:
        cmd = "git rev-parse HEAD"
        result = subprocess.run(shlex.split(cmd), stdout=subprocess.PIPE)
        return result.stdout.decode("utf-8").strip()
    except:
        return "unknown"

def domain_to_stackname(domain):
    """Create a CloudFormation Stackname from domain name by removing '.' and
    capitalizing each part of the domain.
    """
    return "".join(map(lambda x: x.capitalize(), domain.split(".")))

def template_argument(key, value, use_previous = False):
    """Create a JSON dictionary formated as a CloudFlormation template
    argument.

    use_previous is passed as UserPreviousValue to CloudFlormation.
    """
    return {"ParameterKey": key, "ParameterValue": value, "UsePreviousValue": use_previous}

def keypair_to_file(keypair):
    """Look for a ssh key named <keypair> and alert if it does not exist."""
    file = os.path.expanduser("~/.ssh/{}.pem".format(keypair))
    if not os.path.exists(file):
        print("Error: SSH Key '{}' does not exist".format(file))
        return None
    return file

def call_vault(session, bastion_key, bastion_host, vault_host, command, *args, **kwargs):
    """Call ../vault/bastion.py with a list of hardcoded AWS / SSH arguments.
    This is a common function for any other function that needs to populate
    or provision Vault when starting up new VMs.
    """
    bastion_ip = bastion.machine_lookup(session, bastion_host)
    vault_ip = bastion.machine_lookup(session, vault_host, public_ip = False)
    def cmd():
        # Have to dynamically lookup the function because vault.COMMANDS
        # references the command line version of the commands we want to execute
        return vault.__dict__[command.replace('-','_')](*args, machine=vault_host, **kwargs)

    return bastion.connect_vault(bastion_key, vault_ip, bastion_ip, cmd)

def password(what):
    """Prompt the user for a password and verify it."""
    while True:
        pass_ = getpass.getpass("{} Password: ".format(what))
        pass__ = getpass.getpass("Verify {} Password: ".format(what))
        if pass_ == pass__:
            return pass_
        else:
            print("Passwords didn't match, try again.")

def generate_password(length = 16):
    """Generate an alphanumeric password of the given length."""
    chars = string.ascii_letters + string.digits #+ string.punctuation
    return "".join([chars[c % len(chars)] for c in os.urandom(length)])

def vpc_id_lookup(session, vpc_domain):
    """Lookup the Id for the VPC with the given domain name."""
    if session is None: return None

    client = session.client('ec2')
    response = client.describe_vpcs(Filters=[{"Name":"tag:Name", "Values":[vpc_domain]}])
    if len(response['Vpcs']) == 0:
        return None
    else:
        return response['Vpcs'][0]['VpcId']

def subnet_id_lookup(session, subnet_domain):
    """Lookup the Id for the Subnet with the given domain name."""
    if session is None: return None

    client = session.client('ec2')
    response = client.describe_subnets(Filters=[{"Name":"tag:Name", "Values":[subnet_domain]}])
    if len(response['Subnets']) == 0:
        return None
    else:
        return response['Subnets'][0]['SubnetId']

def azs_lookup(session):
    """Lookup all of the Availablity Zones for the connected region."""
    if session is None: return []

    client = session.client('ec2')
    response = client.describe_availability_zones()
    rtn = [(z["ZoneName"], z["ZoneName"][-1]) for z in response["AvailabilityZones"]]

    return rtn

def _find(xs, predicate):
    for x in xs:
        if predicate(x):
            return x
    return None

def ami_lookup(session, ami_name):
    """Lookup the Id for the AMI with the given name."""
    if session is None: return None

    if ami_name.endswith(".boss"):
        AMI_VERSION = os.environ["AMI_VERSION"]
        if AMI_VERSION == "latest":
            ami_name += "-*"
        else:
            ami_name += "-" + AMI_VERSION

    client = session.client('ec2')
    response = client.describe_images(Filters=[{"Name":"name", "Values":[ami_name]}])
    if len(response['Images']) == 0:
        return None
    else:
        response['Images'].sort(key=lambda x: x["CreationDate"], reverse=True)
        image = response['Images'][0]
        ami = image['ImageId']
        tag = _find(image.get('Tags',[]), lambda x: x["Key"] == "Commit")
        commit = None if tag is None else tag["Value"]

        return (ami, commit)

def sg_lookup(session, vpc_id, group_name):
    """Lookup the Id for the VPC Security Group with the given name."""
    if session is None: return None

    client = session.client('ec2')
    response = client.describe_security_groups(Filters=[{"Name":"vpc-id", "Values":[vpc_id]},
                                                        {"Name":"tag:Name", "Values":[group_name]}])

    if len(response['SecurityGroups']) == 0:
        return None
    else:
        return response['SecurityGroups'][0]['GroupId']

def rt_lookup(session, vpc_id, rt_name):
    """Lookup the Id for the VPC Route Table with the given name."""
    if session is None: return None

    client = session.client('ec2')
    response = client.describe_route_tables(Filters=[{"Name":"vpc-id", "Values":[vpc_id]},
                                                     {"Name":"tag:Name", "Values":[rt_name]}])

    if len(response['RouteTables']) == 0:
        return None
    else:
        return response['RouteTables'][0]['RouteTableId']

def rt_name_default(session, vpc_id, new_rt_name):
    """Find the default VPC Route Table and give it a name so that it can be referenced latter.
    Needed because by default the Route Table does not have a name and rt_lookup() will not find it. """

    client = session.client('ec2')
    response = client.describe_route_tables(Filters=[{"Name":"vpc-id", "Values":[vpc_id]}])
    rt_id = response['RouteTables'][0]['RouteTableId'] # TODO: verify that Tags does not already have a name tag

    resource = session.resource('ec2')
    rt = resource.RouteTable(rt_id)
    response = rt.create_tags(Tags=[{"Key": "Name", "Value": new_rt_name}])

def peering_lookup(session, from_id, to_id):
    """Lookup the Id for the Peering Connection between the two VPCs."""
    if session is None: return None

    client = session.client('ec2')
    response = client.describe_vpc_peering_connections(Filters=[{"Name":"requester-vpc-info.vpc-id", "Values":[from_id]},
                                                                {"Name":"requester-vpc-info.owner-id", "Values":["256215146792"]},
                                                                {"Name":"accepter-vpc-info.vpc-id", "Values":[to_id]},
                                                                {"Name":"accepter-vpc-info.owner-id", "Values":["256215146792"]},
                                                                {"Name":"status-code", "Values":["active"]},
                                                                ])

    if len(response['VpcPeeringConnections']) == 0:
        return None
    else:
        return response['VpcPeeringConnections'][0]['VpcPeeringConnectionId']

def keypair_lookup(session):
    """Print the valid key pairs for the session and ask the user which to use."""
    if session is None: return None

    client = session.client('ec2')
    response = client.describe_key_pairs()
    print("Key Pairs")
    for i in range(len(response['KeyPairs'])):
        print("{}:  {}".format(i, response['KeyPairs'][i]['KeyName']))
    if len(response['KeyPairs']) == 0:
        return None
    while True:
        try:
            idx = input("[0]: ")
            idx = int(idx if len(idx) > 0 else "0")
            return response['KeyPairs'][idx]['KeyName']
        except:
            print("Invalid Key Pair number, try again")

def instanceid_lookup(session, hostname):
    """Look up instance id by hostname."""
    if session is None: return None

    client = session.client('ec2')
    response = client.describe_instances(
        Filters=[{"Name":"tag:Name", "Values":[hostname]}])

    item = response['Reservations']
    if len(item) == 0:
        return None
    else:
        item = item[0]['Instances']
        if len(item) == 0:
            return None
        else:
            item = item[0]
            if 'InstanceId' in item:
                return item['InstanceId']
            return None
