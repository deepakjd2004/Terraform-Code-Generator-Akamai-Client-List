# ----------------------------------------------------------------------------------------------------------------------------------------------------------------------------------
# PURPOSE - Run this script to generate terraform code to import existing client lists into terraform stack.
# ----------------------------------------------------------------------------------------------------------------------------------------------------------------------------------
# HOW TO USE THE SCRIPT :
# Step 1 - Create config.yaml file - This file needs to have information about contract, group and client list that needs to be managed with terraform. Check the sample config.yaml
# Step 2 - Run this script i.e. python generate_client_list_tf_code.py
# Step 3 - once generate_client_list_tf_code.py completes, you should have import.sh, variables.tf and main.tf file created. If edgerc section you are targeting is other then defaul then update variables.tf file.
# Step 4 - Run import.sh to import the networklist. This will generate terraform state file with resources
# Step 5 - start managing resources using terraform.
# ----------------------------------------------------------------------------------------------------------------------------------------------------------------------------------
# PRE-REQUISITE - 
# 1) API credential setup correctly
# 2) Python 3 
# 3) Install these python packages(latest should be fine) using pip or other methods - pyYaml, requests, akamai.edgegrid, urllib and logging.
# **********************************************************************************************************************************************************************************

import yaml
import requests
import json
from akamai.edgegrid import EdgeGridAuth, EdgeRc
from urllib.parse import urljoin
from os.path import expanduser
# import logging

# Configure logging
#logging.basicConfig(level=logging.DEBUG)
#logger = logging.getLogger()

# Define your API endpoint and authentication details
edgerc_path = expanduser("~")
edgerc_file = f"{edgerc_path}/.edgerc"
edgerc = EdgeRc(edgerc_file)
section = 'default'
baseurl = f'https://{edgerc.get(section, "host")}'
session = requests.Session()
session.auth = EdgeGridAuth.from_edgerc(edgerc, section)
session.headers.update({'User-Agent': "AkamaiCLI"})
headers = {'Accept-Type': 'application/json', 'Accept': 'application/json', 'accept': 'application/json'}
params = {}

# Load config.yaml 
def load_yaml(file_path):
    with open(file_path, 'r') as file:
        return yaml.safe_load(file)

# Get list details from backend API
def fetch_client_list_data():
    resourcesDetailEp = '/client-list/v1/lists?includeItems=true'
    response = session.get(urljoin(baseurl, resourcesDetailEp))
    if response.status_code >= 400:
        print("Failure extracting details of client lists")
        raise Exception("fetch_client_list_data function failed with status code: {}".format(response.status_code))
    return response.json()

# This functions is responsible for generating terraform code.
def generate_terraform_code(lists, contract_id, groups):
    terraform_code = []
    import_commands = []
    activation_code = []

    # Create a dictionary to map list names to their details
    list_info = {lst['name']: lst for lst in lists}

    for group in groups:
        group_id = group['group_id']
        lists_in_group = group['lists']

        for list_name in lists_in_group:
            lst = list_info.get(list_name)
            if not lst:
                continue

            terraform_name = ''.join(c if c.isalnum() or c == '_' else '_' for c in list_name)
            terraform_code.append(f'resource "akamai_clientlist_list" "{terraform_name}" {{')
            
            # Add tags if they exist
            if 'tags' in lst and lst['tags']:
                terraform_code.append(f'  tags        = {json.dumps(lst["tags"])}')
             
            # Add notes if they exist
            if 'notes' in lst and lst['notes']:
                terraform_code.append(f'  notes       = "{lst["notes"]}"')

            terraform_code.append(f'  name        = "{list_name}"')
            terraform_code.append(f'  type        = "{lst["type"]}"')
            terraform_code.append(f'  contract_id = "{contract_id}"')
            terraform_code.append(f'  group_id    = {group_id}')
            
            for item in lst.get('items', []):
                terraform_code.append('  items {')
                terraform_code.append(f'    value           = "{item["value"]}"')
                if 'tags' in item and item['tags']:
                    terraform_code.append(f'    tags            = {json.dumps(item["tags"])}')
                if 'description' in item and item['description']:
                    terraform_code.append(f'    description     = "{item["description"]}"')
                if 'expirationDate' in item and item['expirationDate']:
                    terraform_code.append(f'    expiration_date = "{item["expirationDate"]}"')
                terraform_code.append('  }')
            
            terraform_code.append('}')
            terraform_code.append('')  # Blank line for separation
            
            import_commands.append(f'terraform import akamai_clientlist_list.{terraform_name} {lst["listId"]}')
            
            # Generate activation blocks based on statuses
            if lst['productionActivationStatus'] == 'ACTIVE':
                activation_code.append(f'resource "akamai_clientlist_activation" "{terraform_name}_prod" {{')
                activation_code.append(f'  list_id                 = "{lst["listId"]}"')
                activation_code.append(f'  version                 = akamai_clientlist_list.{terraform_name}.version')
                activation_code.append(f'  network                 = "PRODUCTION"')
                activation_code.append(f'  comments                = var.comments')
                activation_code.append(f'  notification_recipients = var.email')
                activation_code.append('}')
                activation_code.append('')
                import_commands.append(f'terraform import akamai_clientlist_activation.{terraform_name}_prod {lst["listId"]+":PRODUCTION"}')
            
            if lst['stagingActivationStatus'] == 'ACTIVE':
                activation_code.append(f'resource "akamai_clientlist_activation" "{terraform_name}_staging" {{')
                activation_code.append(f'  list_id                 = "{lst["listId"]}"')
                activation_code.append(f'  version                 = akamai_clientlist_list.{terraform_name}.version')
                activation_code.append(f'  network                 = "STAGING"')
                activation_code.append(f'  comments                = var.comments')
                activation_code.append(f'  notification_recipients = var.email')
                activation_code.append('}')
                activation_code.append('')
                import_commands.append(f'terraform import akamai_clientlist_activation.{terraform_name}_staging {lst["listId"]+":STAGING"}')
    
    return terraform_code, import_commands, activation_code

# This function generate static variables.tf file
def write_variable_file():
    variable_definitions = [
        'variable "edgerc_path" {',
        '  type    = string',
        '  default = "~/.edgerc"',
        '}',
        '',
        'variable "comments" {',
        '  type    = string',
        '  default = "updated via TF"',
        '}',
        '',
        'variable "email" {',
        '  type    = list',
        '  default = []',
        '}',
        '',
        'variable "config_section" {',
        '  type    = string',
        '  default = "default"',
        '}',
        '',
        'variable "env" {',
        '  type    = string',
        '  default = "staging"',
        '}',
        ''
    ]

    with open('variables.tf', 'w') as file:
        file.write('\n'.join(variable_definitions))

def main():
    yaml_file = 'config.yaml'
    config = load_yaml(yaml_file)
    contract_id = config['contract_id']
    groups = config['groups']

    data = fetch_client_list_data()
    lists = data.get('content', [])

    terraform_code, import_commands, activation_code = generate_terraform_code(lists, contract_id, groups)
    
    static_blocks = [
        'terraform {',
        '  required_providers {',
        '    akamai = {',
        '      source  = "akamai/akamai"',
        '      version = ">= 3.5.0"',
        '    }',
        '  }',
        '  required_version = ">= 0.13"',
        '}',
        '',
        'provider "akamai" {',
        '  edgerc         = var.edgerc_path',
        '  config_section = var.config_section',
        '}',
        ''
    ]

    with open('main.tf', 'w') as file:
        file.write('\n'.join(static_blocks))
        file.write('\n')
        file.write('\n'.join(terraform_code))
        file.write('\n')
        file.write('\n'.join(activation_code))
    
    with open('import.sh', 'w') as file:
        file.write('terraform init\n')
        file.write('\n'.join(import_commands))
    
    write_variable_file()

    print("Terraform configuration has been generated and saved to main.tf")
    print("Import commands have been generated and saved to import.sh")
    print("Variables have been generated and saved to variables.tf")

if __name__ == '__main__':
    main()
