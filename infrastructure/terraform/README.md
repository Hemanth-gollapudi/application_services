# AWS Infrastructure with Terraform

This directory contains Terraform configurations to deploy the application services to AWS EC2.

## Prerequisites

1. [Terraform](https://www.terraform.io/downloads.html) installed (v1.0.0 or newer)
2. AWS CLI installed and configured with appropriate credentials
3. SSH key pair created in AWS

## Configuration

1. Create a `terraform.tfvars` file with your specific values:

```hcl
aws_region    = "us-east-1"  # Your preferred AWS region
key_name      = "your-key-name"  # Your SSH key pair name
git_repo_url  = "https://github.com/your-username/application_services.git"
```

## Usage

1. Initialize Terraform:

```bash
terraform init
```

2. Review the deployment plan:

```bash
terraform plan
```

3. Apply the configuration:

```bash
terraform apply
```

4. When finished, destroy the infrastructure:

```bash
terraform destroy
```

## Infrastructure Components

The configuration creates:

- VPC with public subnet
- Internet Gateway
- Route Table
- Security Group
- EC2 instance with:
  - Docker
  - Docker Compose
  - kubectl
  - Application services running in containers

## Outputs

After successful deployment, you'll see:

- Instance public IP
- Instance public DNS
- Application URL
- Keycloak URL
- VPC ID

## Security Notes

- The security group allows inbound traffic on ports 22 (SSH), 80 (HTTP), 443 (HTTPS), and 8009 (Application)
- Make sure to restrict the CIDR blocks in the security group for production use
- Consider using AWS Secrets Manager for sensitive information

## Customization

Modify `variables.tf` to change:

- Instance type
- AMI ID
- VPC CIDR
- Subnet CIDR
- Other deployment parameters
