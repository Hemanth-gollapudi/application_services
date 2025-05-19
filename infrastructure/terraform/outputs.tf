output "instance_public_ip" {
  description = "Public IP address of the EC2 instance"
  value       = aws_instance.app_server.public_ip
}

output "instance_public_dns" {
  description = "Public DNS name of the EC2 instance"
  value       = aws_instance.app_server.public_dns
}

output "elastic_ip" {
  description = "Elastic IP address attached to the EC2 instance"
  value       = aws_eip.app_eip.public_ip
}

output "application_url" {
  description = "URL for accessing the application"
  value       = "http://${aws_eip.app_eip.public_ip}:${var.app_port}"
}

output "keycloak_url" {
  description = "URL for accessing Keycloak"
  value       = "http://${aws_eip.app_eip.public_ip}:${var.keycloak_port}"
}

output "private_key_path" {
  description = "Path to the private key file"
  value       = local_file.private_key.filename
}

output "ssh_command" {
  description = "SSH command to connect to the instance"
  value       = "ssh -i ${local_file.private_key.filename} ec2-user@${aws_eip.app_eip.public_ip}"
}

output "vpc_id" {
  description = "ID of the VPC"
  value       = data.aws_vpc.default.id
}

output "subnet_id" {
  description = "ID of the subnet"
  value       = data.aws_subnet.default.id
}

output "availability_zone" {
  description = "Availability zone of the subnet"
  value       = data.aws_subnet.default.availability_zone
} 