variable "aws_region" {
  description = "AWS region to deploy resources"
  type        = string
  default     = "us-east-1"
}

variable "project_name" {
  description = "Name of the project"
  type        = string
  default     = "application-services"
}

variable "ami_id" {
  description = "AMI ID for EC2 instance (Ubuntu 22.04 LTS)"
  type        = string
  default     = "ami-0c7217cdde317cfec"  # Ubuntu 22.04 LTS in us-east-1
}

variable "instance_type" {
  description = "EC2 instance type"
  type        = string
  default     = "t2.medium"
}

variable "git_repo_url" {
  description = "URL of the Git repository"
  type        = string
}

variable "app_port" {
  description = "Port number for the application"
  type        = number
  default     = 3000
}

variable "keycloak_port" {
  description = "Port number for Keycloak"
  type        = number
  default     = 8081
} 