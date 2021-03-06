/**
 * Kubernetes infrastructure for the api.saintsxctf.com application.
 * Author: Andrew Jarombek
 * Date: 7/13/2020
 */

data "aws_caller_identity" "current" {}

data "aws_eks_cluster" "cluster" {
  name = "andrew-jarombek-eks-cluster"
}

data "aws_eks_cluster_auth" "cluster" {
  name = "andrew-jarombek-eks-cluster"
}

data "aws_vpc" "kubernetes-vpc" {
  tags = {
    Name = "kubernetes-vpc"
  }
}

data "aws_subnet" "kubernetes-dotty-public-subnet" {
  tags = {
    Name = "kubernetes-dotty-public-subnet"
  }
}

data "aws_subnet" "kubernetes-grandmas-blanket-public-subnet" {
  tags = {
    Name = "kubernetes-grandmas-blanket-public-subnet"
  }
}

data "aws_acm_certificate" "saintsxctf-cert" {
  domain = local.domain_cert
  statuses = ["ISSUED"]
}

data "aws_acm_certificate" "saintsxctf-wildcard-cert" {
  domain = local.wildcard_domain_cert
  statuses = ["ISSUED"]
}

provider "kubernetes" {
  host = data.aws_eks_cluster.cluster.endpoint
  cluster_ca_certificate = base64decode(data.aws_eks_cluster.cluster.certificate_authority.0.data)
  token = data.aws_eks_cluster_auth.cluster.token
  load_config_file = false
}

#----------------
# Local Variables
#----------------

locals {
  short_env = var.prod ? "prod" : "dev"
  env = var.prod ? "production" : "development"
  namespace = var.prod ? "saints-xctf" : "saints-xctf-dev"
  short_version = "1.0.0"
  version = "v${local.short_version}"
  account_id = data.aws_caller_identity.current.account_id
  domain_cert = "*.api.saintsxctf.com"
  wildcard_domain_cert = "*.dev.api.saintsxctf.com"
  cert_arn = data.aws_acm_certificate.saintsxctf-cert.arn
  wildcard_cert_arn = data.aws_acm_certificate.saintsxctf-wildcard-cert.arn
  subnet1 = data.aws_subnet.kubernetes-dotty-public-subnet.id
  subnet2 = data.aws_subnet.kubernetes-grandmas-blanket-public-subnet.id
}

#--------------
# AWS Resources
#--------------

resource "aws_security_group" "saints-xctf-api-lb-sg" {
  name = "saints-xctf-api-${local.short_env}-lb-security-group"
  vpc_id = data.aws_vpc.kubernetes-vpc.id

  lifecycle {
    create_before_destroy = true
  }

  ingress {
    protocol = "tcp"
    from_port = 80
    to_port = 80
    cidr_blocks = ["0.0.0.0/0"]
  }

  ingress {
    protocol = "tcp"
    from_port = 443
    to_port = 443
    cidr_blocks = ["0.0.0.0/0"]
  }

  egress {
    protocol = "-1"
    from_port = 0
    to_port = 0
    cidr_blocks = ["0.0.0.0/0"]
  }

  tags = {
    Name = "saints-xctf-api-${local.short_env}-lb-security-group"
    Application = "saints-xctf"
    Environment = local.env
  }
}

#---------------------------------------------------
# Kubernetes Resources for the SaintsXCTF Web Server
#---------------------------------------------------

resource "kubernetes_deployment" "deployment" {
  metadata {
    name = "saints-xctf-api-deployment"
    namespace = local.namespace

    labels = {
      version = local.version
      environment = local.env
      application = "saints-xctf-api"
    }
  }

  spec {
    replicas = 1
    min_ready_seconds = 10

    strategy {
      type = "RollingUpdate"

      rolling_update {
        max_surge = "1"
        max_unavailable = "0"
      }
    }

    template {
      metadata {
        labels = {
          version = local.version
          environment = local.env
          application = "saints-xctf-api"
        }
      }

      spec {
        container {
          name = "saints-xctf-api"
          image = "${local.account_id}.dkr.ecr.us-east-1.amazonaws.com/saints-xctf-api:${local.short_version}"

          readiness_probe {
            period_seconds = 5
            initial_delay_seconds = 20

            http_get {
              path = "/"
              port = 5000
            }
          }

          port {
            container_port = 5000
            protocol = "TCP"
          }
        }
      }
    }
  }
}

resource "kubernetes_service" "service" {
  metadata {
    name = "saints-xctf-api-service"
    namespace = local.namespace

    labels = {
      version = local.version
      environment = local.env
      application = "saints-xctf-api"
    }
  }

  spec {
    type = "NodePort"

    port {
      port = 80
      target_port = 5000
      protocol = "TCP"
    }

    selector = {
      application = "saints-xctf-api"
    }
  }
}

resource "kubernetes_ingress" "ingress" {
  metadata {
    name = "saints-xctf-api-ingress"
    namespace = local.namespace

    annotations = {
      "kubernetes.io/ingress.class" = "alb"
      "external-dns.alpha.kubernetes.io/hostname" = "api.saintsxctf.com,www.api.saintsxctf.com"
      "alb.ingress.kubernetes.io/backend-protocol" = "HTTP"
      "alb.ingress.kubernetes.io/certificate-arn" = "${local.cert_arn},${local.wildcard_cert_arn}"
      "alb.ingress.kubernetes.io/healthcheck-path" = "/login"
      "alb.ingress.kubernetes.io/listen-ports" = "[{\"HTTP\":80}, {\"HTTPS\":443}]"
      "alb.ingress.kubernetes.io/healthcheck-protocol": "HTTP"
      "alb.ingress.kubernetes.io/scheme" = "internet-facing"
      "alb.ingress.kubernetes.io/security-groups" = aws_security_group.saints-xctf-api-lb-sg.id
      "alb.ingress.kubernetes.io/subnets" = "${local.subnet1},${local.subnet2}"
      "alb.ingress.kubernetes.io/target-type" = "instance"
      "alb.ingress.kubernetes.io/tags" = "Name=saints-xctf-web-load-balancer,Application=saints-xctf,Environment=${local.env}"
    }

    labels = {
      version = local.version
      environment = local.env
      application = "api.saints-xctf-web"
    }
  }

  spec {
    rule {
      host = "api.saintsxctf.com"

      http {
        path {
          path = "/*"

          backend {
            service_name = "saints-xctf-api-service"
            service_port = 80
          }
        }
      }
    }

    rule {
      host = "www.api.saintsxctf.com"

      http {
        path {
          path = "/*"

          backend {
            service_name = "saints-xctf-api-service"
            service_port = 80
          }
        }
      }
    }
  }
}
