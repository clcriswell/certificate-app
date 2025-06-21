# Example EKS cluster
resource "aws_eks_cluster" "agent" {
  name     = "agent-cluster"
  role_arn = aws_iam_role.eks.arn

  vpc_config {
    subnet_ids = [aws_subnet.public.id]
  }
}
