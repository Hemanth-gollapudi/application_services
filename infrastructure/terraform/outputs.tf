output "instance_public_ip" {
  description = "Public IP address of the EC2 instance (Elastic IP)"
  value       = aws_eip.app_eip.public_ip
}

output "instance_public_dns" {
  description = "Public DNS name of the EC2 instance"
  value       = aws_instance.app_server.public_dns
}

output "elastic_ip" {
  description = "Elastic IP address assigned to the instance"
  value       = aws_eip.app_eip.public_ip
}

output "application_url" {
  description = "URL to access the application"
  value       = "http://${aws_eip.app_eip.public_ip}:8009"
}

output "keycloak_url" {
  description = "URL to access Keycloak"
  value       = "http://${aws_eip.app_eip.public_ip}:8084"
}

output "private_key_path" {
  description = "Path to the private key file"
  value       = local_file.private_key.filename
}

output "ssh_command" {
  description = "SSH command to connect to the instance"
  value       = "ssh -i ${local_file.private_key.filename} ubuntu@${aws_eip.app_eip.public_ip}"
}

output "subnet_id" {
  description = "ID of the subnet used"
  value       = data.aws_subnet.selected.id
}

output "vpc_id" {
  description = "ID of the VPC used"
  value       = data.aws_vpc.default.id
} 