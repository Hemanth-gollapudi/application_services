output "instance_public_ip" {
  description = "Public IP address of the EC2 instance"
  value       = aws_instance.app_server.public_ip
}

output "instance_public_dns" {
  description = "Public DNS name of the EC2 instance"
  value       = aws_instance.app_server.public_dns
}

output "vpc_id" {
  description = "ID of the VPC"
  value       = aws_vpc.app_vpc.id
}

output "application_url" {
  description = "URL to access the application"
  value       = "http://${aws_instance.app_server.public_dns}:8009"
}

output "keycloak_url" {
  description = "URL to access Keycloak"
  value       = "http://${aws_instance.app_server.public_dns}:8084"
} 