# DB Subnet Group across private subnets
resource "aws_db_subnet_group" "rds" {
  name       = "${var.app_name}-db-subnet-group"
  subnet_ids = aws_subnet.private[*].id

  tags = {
    Name = "${var.app_name}-db-subnet-group"
  }
}

# Amazon RDS PostgreSQL Instance (pgvector supported out of the box in Postgres 15+)
resource "aws_db_instance" "postgres" {
  identifier             = "${var.app_name}-postgres"
  engine                 = "postgres"
  engine_version         = "15.13"
  instance_class         = var.db_instance_class
  allocated_storage      = 20
  max_allocated_storage  = 100
  storage_type           = "gp3"
  
  db_name                = var.db_name
  username               = var.db_username
  password               = var.db_password
  
  db_subnet_group_name   = aws_db_subnet_group.rds.name
  vpc_security_group_ids = [aws_security_group.rds.id]

  skip_final_snapshot    = true
  publicly_accessible    = false
  deletion_protection    = false

  tags = {
    Name = "${var.app_name}-rds-pgvector"
  }
}
