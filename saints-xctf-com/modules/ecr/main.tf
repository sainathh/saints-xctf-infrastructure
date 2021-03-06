/**
 * Docker image repositories in Elastic Container Registry for the SaintsXCTF application.
 * Author: Andrew Jarombek
 * Date: 7/13/2020
 */

resource "aws_ecr_repository" "saints-xctf-web-repository" {
  name = "saints-xctf-web"
  image_tag_mutability = "MUTABLE"

  image_scanning_configuration {
    scan_on_push = true
  }

  tags = {
    Name = "saints-xctf-web-container-repository"
    Application = "all"
    Environment = "all"
  }
}