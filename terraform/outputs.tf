output "alb_dns_name" {
  description = "Public DNS name of the Application Load Balancer"
  value       = aws_lb.main.dns_name
}

output "application_url" {
  description = "Live Application URL (Frontend & API routed via ALB)"
  value       = "http://${aws_lb.main.dns_name}"
}

output "api_endpoint" {
  description = "FastAPI backend base endpoint"
  value       = "http://${aws_lb.main.dns_name}/api"
}

output "rds_postgres_endpoint" {
  description = "PostgreSQL RDS endpoint with pgvector"
  value       = aws_db_instance.postgres.endpoint
}

output "backend_ecr_repository_url" {
  description = "ECR Repository URL for Backend image"
  value       = aws_ecr_repository.backend.repository_url
}

output "frontend_ecr_repository_url" {
  description = "ECR Repository URL for Frontend image"
  value       = aws_ecr_repository.frontend.repository_url
}
