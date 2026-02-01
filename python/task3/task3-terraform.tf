###########################################################################
# Template for Task 3 AWS AutoScaling Test                                #
# Do not edit the first section                                           #
# Only edit the second section to configure appropriate scaling policies  #
###########################################################################

############################
# FIRST SECTION BEGINS     #
# DO NOT EDIT THIS SECTION #
############################
locals {
  common_tags = {
    Project = "vm-scaling"
  }
  asg_tags = {
    key                 = "Project"
    value               = "vm-scaling"
    propagate_at_launch = true
  }
}

provider "aws" {
  region = "us-east-1"
}


resource "aws_security_group" "lg" {
  # HTTP access from anywhere
  ingress {
    from_port   = 80
    to_port     = 80
    protocol    = "tcp"
    cidr_blocks = ["0.0.0.0/0"]
  }

  # outbound internet access
  egress {
    from_port   = 0
    to_port     = 0
    protocol    = "-1"
    cidr_blocks = ["0.0.0.0/0"]
  }

  tags = local.common_tags
}

resource "aws_security_group" "elb_asg" {
  # HTTP access from anywhere
  ingress {
    from_port   = 80
    to_port     = 80
    protocol    = "tcp"
    cidr_blocks = ["0.0.0.0/0"]
  }

  # outbound internet access
  egress {
    from_port   = 0
    to_port     = 0
    protocol    = "-1"
    cidr_blocks = ["0.0.0.0/0"]
  }

  tags = local.common_tags
}

######################
# FIRST SECTION ENDS #
######################

############################
# SECOND SECTION BEGINS    #
# PLEASE EDIT THIS SECTION #
############################

# =========================================================================
# PRE-REQUISITES: VPC & SUBNETS
# =========================================================================
# I need the default VPC and Subnets to place the resources in.
resource "aws_default_vpc" "default" {
  tags = {
    Name = "Default VPC"
  }
}

# Subnet for ASG (us-east-1a)
resource "aws_default_subnet" "default_az1" {
  availability_zone = "us-east-1a"
}

# Second Subnet for ALB (ALBs require 2 AZs usually)
resource "aws_default_subnet" "default_az2" {
  availability_zone = "us-east-1b"
}

# Step 1:
# ================================
resource "aws_launch_template" "lt" {
  name          = "Web-LaunchTemplate"
  image_id      = "ami-0e3d567ccafde16c5"
  instance_type = "m5.large"

  monitoring {
    enabled = true
  }

  vpc_security_group_ids = [aws_security_group.elb_asg.id]

  tag_specifications {
    resource_type = "instance"
    tags = {
      Project = "vm-scaling"
    }
  }
}

# Create an auto scaling group with appropriate parameters
resource "aws_autoscaling_group" "asg" {
  availability_zones        = ["us-east-1a"]
  max_size                  = 4
  min_size                  = 1
  desired_capacity          = 1
  default_cooldown          = 60     # Default safety buffer
  health_check_grace_period = 60
  health_check_type         = "EC2"  # As requested in the task prompt list
  
  launch_template {
    id      = aws_launch_template.lt.id
    version = "$Latest"
  }
  
  # Link to the Target Group (defined in Step 2)
  target_group_arns         = [aws_lb_target_group.asg_tg.arn]
  
  tag {
    key                 = local.asg_tags.key
    value               = local.asg_tags.value
    propagate_at_launch = local.asg_tags.propagate_at_launch
  }
}

# Create a Load Generator AWS instance
resource "aws_instance" "load_generator" {
  ami           = "ami-0469ff4742c562d63"
  instance_type = "m5.large"
  subnet_id     = aws_default_subnet.default_az1.id
  
  # Attach the LG Security Group
  vpc_security_group_ids = [aws_security_group.lg.id]

  tags = local.common_tags
}

# Step 2:
# ================================
# Application Load Balancer
resource "aws_lb" "web_alb" {
  name               = "Web-LoadBalancer"
  internal           = false
  load_balancer_type = "application"
  security_groups    = [aws_security_group.elb_asg.id]
  # ALBs need subnets. Using the default ones defined above.
  subnets            = [aws_default_subnet.default_az1.id, aws_default_subnet.default_az2.id]

  tags = local.common_tags
}

# Target Group
resource "aws_lb_target_group" "asg_tg" {
  name     = "ASG-TargetGroup"
  port     = 80
  protocol = "HTTP"
  vpc_id   = aws_default_vpc.default.id

  health_check {
    path                = "/"
    protocol            = "HTTP"
    matcher             = "200"
    interval            = 10
    timeout             = 5
    healthy_threshold   = 2
    unhealthy_threshold = 2
  }
}

# Listener (Forward HTTP:80 -> Target Group)
resource "aws_lb_listener" "web_listener" {
  load_balancer_arn = aws_lb.web_alb.arn
  port              = "80"
  protocol          = "HTTP"

  default_action {
    type             = "forward"
    target_group_arn = aws_lb_target_group.asg_tg.arn
  }
}

# Step 3:
# ================================
# Scale Out Policy (High Velocity: 15s Cooldown, +1 Instance)
resource "aws_autoscaling_policy" "scale_out" {
  name                   = "Scale Out Policy"
  scaling_adjustment     = 1
  adjustment_type        = "ChangeInCapacity"
  cooldown               = 15
  autoscaling_group_name = aws_autoscaling_group.asg.name
  policy_type            = "SimpleScaling"
}

# Scale In Policy (High Velocity: 15s Cooldown, -1 Instance)
resource "aws_autoscaling_policy" "scale_in" {
  name                   = "Scale In Policy"
  scaling_adjustment     = -1
  adjustment_type        = "ChangeInCapacity"
  cooldown               = 15
  autoscaling_group_name = aws_autoscaling_group.asg.name
  policy_type            = "SimpleScaling"
}

# Step 4:
# ================================
# Scale Out Alarm (> 60% CPU)
resource "aws_cloudwatch_metric_alarm" "high_cpu" {
  alarm_name          = "High-CPU-Alarm"
  comparison_operator = "GreaterThanThreshold"
  evaluation_periods  = "1"
  metric_name         = "CPUUtilization"
  namespace           = "AWS/EC2"
  period              = "60"
  statistic           = "Average"
  threshold           = "60"

  dimensions = {
    AutoScalingGroupName = aws_autoscaling_group.asg.name
  }

  alarm_description = "Scale out if CPU > 60%"
  alarm_actions     = [aws_autoscaling_policy.scale_out.arn]
}

# Scale In Alarm (< 20% CPU)
resource "aws_cloudwatch_metric_alarm" "low_cpu" {
  alarm_name          = "Low-CPU-Alarm"
  comparison_operator = "LessThanThreshold"
  evaluation_periods  = "1"
  metric_name         = "CPUUtilization"
  namespace           = "AWS/EC2"
  period              = "60"
  statistic           = "Average"
  threshold           = "20"

  dimensions = {
    AutoScalingGroupName = aws_autoscaling_group.asg.name
  }

  alarm_description = "Scale in if CPU < 20%"
  alarm_actions     = [aws_autoscaling_policy.scale_in.arn]
}

######################################
# SECOND SECTION ENDS                #
# MAKE SURE YOU COMPLETE ALL 4 STEPS #
######################################