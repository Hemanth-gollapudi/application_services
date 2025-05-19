terraform {
  required_providers {
    aws = {
      source  = "hashicorp/aws"
      version = "~> 5.0"
    }
    tls = {
      source  = "hashicorp/tls"
      version = "~> 4.0"
    }
    local = {
      source  = "hashicorp/local"
      version = "~> 2.0"
    }
  }
  required_version = ">= 1.2.0"
}

provider "aws" {
  region = var.aws_region
}

# Get all availability zones
data "aws_availability_zones" "available" {
  state = "available"
}

# Get default VPC
data "aws_vpc" "default" {
  default = true
}

# Get existing subnets in the VPC
data "aws_subnets" "default" {
  filter {
    name   = "vpc-id"
    values = [data.aws_vpc.default.id]
  }
}

# Get the first available subnet
data "aws_subnet" "default" {
  id = tolist(data.aws_subnets.default.ids)[0]
}

# Generate private key
resource "tls_private_key" "app_private_key" {
  algorithm = "RSA"
  rsa_bits  = 4096
}

# Store private key locally
resource "local_file" "private_key" {
  content         = tls_private_key.app_private_key.private_key_pem
  filename        = "./application-services-key.pem"
  file_permission = "0600"
}

# Create a new key pair
resource "aws_key_pair" "app_key_pair" {
  key_name   = "application-services-key"
  public_key = tls_private_key.app_private_key.public_key_openssh

  lifecycle {
    create_before_destroy = true
  }
}

# Security Group for Application
resource "aws_security_group" "app_sg" {
  name        = "application-services-sg"
  description = "Security group for application services"
  vpc_id      = data.aws_vpc.default.id

  # Allow HTTP
  ingress {
    from_port   = 80
    to_port     = 80
    protocol    = "tcp"
    cidr_blocks = ["0.0.0.0/0"]
    description = "Allow HTTP traffic"
  }

  # Allow HTTPS
  ingress {
    from_port   = 443
    to_port     = 443
    protocol    = "tcp"
    cidr_blocks = ["0.0.0.0/0"]
    description = "Allow HTTPS traffic"
  }

  # Allow Application Port
  ingress {
    from_port   = var.app_port
    to_port     = var.app_port
    protocol    = "tcp"
    cidr_blocks = ["0.0.0.0/0"]
    description = "Allow Application traffic"
  }

  # Allow Keycloak Port
  ingress {
    from_port   = var.keycloak_port
    to_port     = var.keycloak_port
    protocol    = "tcp"
    cidr_blocks = ["0.0.0.0/0"]
    description = "Allow Keycloak traffic"
  }

  # Allow SSH
  ingress {
    from_port   = 22
    to_port     = 22
    protocol    = "tcp"
    cidr_blocks = ["0.0.0.0/0"]
    description = "Allow SSH access"
  }

  # Allow PostgreSQL
  ingress {
    from_port   = 5434
    to_port     = 5434
    protocol    = "tcp"
    cidr_blocks = ["0.0.0.0/0"]
    description = "Allow PostgreSQL traffic"
  }

  # Allow all outbound traffic
  egress {
    from_port   = 0
    to_port     = 0
    protocol    = "-1"
    cidr_blocks = ["0.0.0.0/0"]
    description = "Allow all outbound traffic"
  }

  tags = {
    Name = "${var.project_name}-sg"
  }

  lifecycle {
    create_before_destroy = true
  }
}

# EC2 Instance
resource "aws_instance" "app_server" {
  ami           = var.ami_id
  instance_type = var.instance_type
  subnet_id     = data.aws_subnet.default.id
  key_name      = aws_key_pair.app_key_pair.key_name

  vpc_security_group_ids = [aws_security_group.app_sg.id]

  root_block_device {
    volume_size = 30
    volume_type = "gp3"
    encrypted   = true
    tags = {
      Name = "application-services-root-volume"
    }
  }

  tags = {
    Name    = "application-services-server"
    Project = "application-services"
  }

  user_data = base64encode(<<-EOF
              #!/bin/bash
              # Install Docker
              yum update -y
              yum install -y docker
              systemctl start docker
              systemctl enable docker
              usermod -aG docker ec2-user

              # Install Docker Compose
              curl -L "https://github.com/docker/compose/releases/latest/download/docker-compose-$(uname -s)-$(uname -m)" -o /usr/local/bin/docker-compose
              chmod +x /usr/local/bin/docker-compose

              # Install kubectl
              curl -LO "https://dl.k8s.io/release/$(curl -L -s https://dl.k8s.io/release/stable.txt)/bin/linux/amd64/kubectl"
              chmod +x kubectl
              mv kubectl /usr/local/bin/
              EOF
  )

  depends_on = [aws_key_pair.app_key_pair]
}

# Elastic IP for EC2 Instance
resource "aws_eip" "app_eip" {
  instance = aws_instance.app_server.id
  domain   = "vpc"
  tags = {
    Name = "application-services-eip"
  }
} 