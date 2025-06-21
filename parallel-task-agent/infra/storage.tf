resource "aws_s3_bucket" "logs" {
  bucket = "agent-audit-logs"
  force_destroy = true
}
