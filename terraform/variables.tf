variable "aws_region" {
  description = "AWS region to deploy resources"
  type        = string
  default     = "ap-south-1" # Mumbai (closest to Indian exchanges NSE/BSE)
}

variable "environment" {
  description = "Deployment environment"
  type        = string
  default     = "production"
}

variable "app_name" {
  description = "Name prefix for all resources"
  type        = string
  default     = "indian-equity-analyst"
}

# Networking
variable "vpc_cidr" {
  description = "CIDR block for VPC"
  type        = string
  default     = "10.0.0.0/16"
}

variable "availability_zones" {
  description = "Availability zones for multi-AZ high availability"
  type        = list(string)
  default     = ["ap-south-1a", "ap-south-1b"]
}

variable "public_subnet_cidrs" {
  description = "CIDR blocks for public subnets"
  type        = list(string)
  default     = ["10.0.1.0/24", "10.0.2.0/24"]
}

variable "private_subnet_cidrs" {
  description = "CIDR blocks for private subnets (RDS and ECS)"
  type        = list(string)
  default     = ["10.0.10.0/24", "10.0.20.0/24"]
}

# Database (RDS PostgreSQL with pgvector)
variable "db_name" {
  description = "PostgreSQL database name"
  type        = string
  default     = "indian_stocks_db"
}

variable "db_username" {
  description = "Master username for RDS Postgres"
  type        = string
  default     = "analyst_admin"
}

variable "db_password" {
  description = "Master password for RDS Postgres"
  type        = string
  sensitive   = true
  default     = "SentellentSecurePass2026!"
}

variable "db_instance_class" {
  description = "RDS instance class"
  type        = string
  default     = "db.t4g.micro"
}

# ECS Fargate
variable "backend_cpu" {
  description = "Fargate CPU units for Backend task (1 vCPU = 1024)"
  type        = number
  default     = 512
}

variable "backend_memory" {
  description = "Fargate memory (MB) for Backend task"
  type        = number
  default     = 1024
}

variable "frontend_cpu" {
  description = "Fargate CPU units for Frontend task"
  type        = number
  default     = 256
}

variable "frontend_memory" {
  description = "Fargate memory (MB) for Frontend task"
  type        = number
  default     = 512
}
