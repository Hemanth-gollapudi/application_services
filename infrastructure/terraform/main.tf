provider "aws" {
  region = var.aws_region
}

# Create a new key pair
resource "aws_key_pair" "app_key_pair" {
  key_name   = "${var.project_name}-key"
  public_key = tls_private_key.app_private_key.public_key_openssh
}

# Generate private key
resource "tls_private_key" "app_private_key" {
  algorithm = "RSA"
  rsa_bits  = 4096
}

# Store private key locally
resource "local_file" "private_key" {
  content         = tls_private_key.app_private_key.private_key_pem
  filename        = "${path.module}/${var.project_name}-key.pem"
  file_permission = "0400"
}

# Get default VPC
data "aws_vpc" "default" {
  default = true
}

# Get default subnet in the first AZ
data "aws_subnet" "default" {
  vpc_id            = data.aws_vpc.default.id
  availability_zone = "${var.aws_region}a"
  default_for_az    = true
}

# Security Group for Application
resource "aws_security_group" "app_sg" {
  name        = "${var.project_name}-sg"
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
    from_port   = 8009
    to_port     = 8009
    protocol    = "tcp"
    cidr_blocks = ["0.0.0.0/0"]
    description = "Allow Application traffic"
  }

  # Allow Keycloak Port
  ingress {
    from_port   = 8084
    to_port     = 8084
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
}

# Elastic IP for EC2 Instance
resource "aws_eip" "app_eip" {
  instance = aws_instance.app_server.id
  domain   = "vpc"

  tags = {
    Name = "${var.project_name}-eip"
  }
}

# EC2 Instance
resource "aws_instance" "app_server" {
  ami           = var.ami_id
  instance_type = var.instance_type
  key_name      = aws_key_pair.app_key_pair.key_name

  subnet_id                   = data.aws_subnet.default.id
  vpc_security_group_ids      = [aws_security_group.app_sg.id]
  associate_public_ip_address = true

  root_block_device {
    volume_size = 30
    volume_type = "gp3"
    encrypted   = true

    tags = {
      Name = "${var.project_name}-root-volume"
    }
  }

  user_data = <<-EOF
              #!/bin/bash
              # Update system packages
              apt-get update
              apt-get upgrade -y

              # Install Docker
              apt-get install -y docker.io
              systemctl start docker
              systemctl enable docker

              # Install Docker Compose
              curl -L "https://github.com/docker/compose/releases/download/v2.20.0/docker-compose-$(uname -s)-$(uname -m)" -o /usr/local/bin/docker-compose
              chmod +x /usr/local/bin/docker-compose

              # Install kubectl
              curl -LO "https://dl.k8s.io/release/$(curl -L -s https://dl.k8s.io/release/stable.txt)/bin/linux/amd64/kubectl"
              chmod +x kubectl
              mv kubectl /usr/local/bin/

              # Clone application repository
              git clone ${var.git_repo_url} /app
              cd /app

              # Set up environment
              cp env.example .env

              # Start services
              docker-compose up -d
              EOF

  tags = {
    Name    = "${var.project_name}-server"
    Project = var.project_name
  }

  # Add this to ensure proper cleanup of the EIP when destroying
  lifecycle {
    create_before_destroy = true
  }
} 