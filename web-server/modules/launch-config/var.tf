/**
 * Variables for the saintsxctf website launch configuration of EC2 instances
 * Author: Andrew Jarombek
 * Date: 12/10/2018
 */

variable "prod" {
  description = "If the environment of the launch configuration is production"
  default = false
}

variable "max_size" {
  description = "Max number of instances in the auto scaling group"
  default = 1
}

variable "min_size" {
  description = "Min number of instances in the auto scaling group"
  default = 1
}

variable "desired_capacity" {
  description = "The desired number of intances in the autoscaling group"
  default = 1
}