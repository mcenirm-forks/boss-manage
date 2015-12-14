"""Create the private parts of the core environment.

DEVICES - the different device configurations to include in the template.
"""

import library as lib
import hosts
import pprint

DEVICES = ["vault"]

def verify_domain(domain):
    """Verify that the given domain is valid in the format 'subnet.vpc.tld'."""
    if len(domain.split(".")) != 3: # subnet.vpc.tld
        raise Exception("Not a valiid Subnet domain name")

def generate(folder, domain):
    """Generate the CloudFormation template and save to disk."""
    verify_domain(domain)
    
    parameters, resources = lib.load_devices(*DEVICES)
    template = lib.create_template(parameters, resources)
    
    lib.save_template(template, folder, "core." + domain)

def create(session, domain):
    """Lookup all of the needed arguments, and create the CloudFormation
    stack.
    """
    verify_domain(domain)

    subnet_id = lib.subnet_id_lookup(session, domain)
    if subnet_id is None:
        raise Exception("Subnet doesn't exists")
    
    keypair = lib.keypair_lookup(session)
    
    args = [
        lib.template_argument("KeyName", keypair),
        lib.template_argument("SubnetId", subnet_id),
        lib.template_argument("VaultAMI", lib.ami_lookup(session, "vault")),
        lib.template_argument("VaultHostname", "vault.core.boss"),
        lib.template_argument("VaultIP", hosts.lookup("vault.core.boss")),
    ]
    
    parameters, resources = lib.load_devices(*DEVICES)
    template = lib.create_template(parameters, resources)
    stack_name = lib.domain_to_stackname("core." + domain)
    
    lib.cloudformation_create(session, stack_name, template, args)