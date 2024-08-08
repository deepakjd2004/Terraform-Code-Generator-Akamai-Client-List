<!-- BEGIN_DOCS -->

# Generate terraform code for managing existing client lists

Akamai terraform cli provides excellent way to export existing delivery/security and other supported product configuration into terraform files but unfortunately client list is not yet part of akamai terraform CLI. Code in this repository helps to mimic the behavior of akamai terraform CLI and extracts client lists from Akamai Control Centre into terraform code on your dev machine.

1. This repo consist of script that reads through input template file and generate terraform code
2. To keep it in sync with akamai terraform cli, it generates files in similar naming convention for e.g. main.tf, variables.tf and import.sh
3. import.sh consist of all the resources that needs to be imported into terraform stack. 
4. Be aware that activation block uses latest version always, if you don't want to always activate the newest version then feel free to modify the main.tf file and put the numbered version or use any other logic to get the version. 

## Purpose
This repository provides a script that automates the generation of terraform code for client list. 


## Authentication & Authorization

1. Identify type of access need for your project - Akamai access control model uses 4 objects namely account,contract, group and resources. You can read about it here https://techdocs.akamai.com/iam/docs/about-access-control-model
2. Provision an API Client - https://techdocs.akamai.com/developer/docs/set-up-authentication-credentials
3. Grab Authentication token -https://techdocs.akamai.com/developer/docs/authenticate-with-edgegrid
4. Give appropriate access

## Usage

1. Clone the repository, using following command:

```bash
> git clone https://github.com/deepakjd2004/Terraform-Code-Generator-Akamai-Client-List
> cd Terraform-Code-Generator-Akamai-Client-List
```

2. Modify `config.yaml` file - This file contains all the inputs that you need to provide to run the script. User needs to provide client lists name (including group and contract id) that needs to be managed via. terraform. 
3. `python generate_client_list_tf_code.py` to run the script. This script creates import.sh, variables.tf and main.tf file. If edgerc section you are targeting is other then default then update section in variables.tf file.
4. Run `. ./import.sh` to import the networklist. This will generate terraform state file with resources
5. All set, now start managing resources using terraform


## Requirements

| Name                                                                     | Version         |
| ------------------------------------------------------------------------ | --------------- |
| <a name="python3.7+"></a> [python3.7+](#python3)                         | >=3.7           |


## Libraries

| Name                                                        | Source                  | Version |
| ----------------------------------------------------------- | ----------------------- | ------- |
| requests                                                    | pip library             | 2.24.0  |
| edgegrid-python                                             | pip library             | 1.1.1   |
| akamaihttp                                                  | pip library             | 0.1     |
| pybase                                                      | pip library             | 1.3.1   |
| pyYaml                                                      | pip library             | 6.0.1   |



<!-- END_DOCS -->
