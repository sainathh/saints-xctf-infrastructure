"""
Functions which represent Unit tests for the web server and launch configuration
Author: Andrew Jarombek
Date: 3/17/2019
"""

import boto3

ec2 = boto3.client('ec2')
sts = boto3.client('sts')
iam = boto3.client('iam')
autoscaling = boto3.client('autoscaling')

"""
Tests for all environments
"""


def ami_exists() -> bool:
    """
    Check if there are one or many AMIs for the SaintsXCTF web server.
    :return: True if there are multiple AMIs, False otherwise
    """
    owner = sts.get_caller_identity().get('Account')
    amis = ec2.describe_images(
        Owners=[owner],
        Filters=[{
            'Name': 'name',
            'Values': ['saints-xctf-web-server*']
        }]
    )
    return len(amis.get('Images')) > 0


"""
Tests for the production environment
"""


def prod_instance_running() -> bool:
    """
    Validate that the EC2 instance(s) holding the production web server are running
    :return: True if the EC2 instance is running, False otherwise
    """
    instances = get_ec2('saints-xctf-server-prod-asg')
    return len(instances) > 0


def prod_instance_not_overscaled() -> bool:
    """
    Ensure that there aren't too many EC2 instances running for the production web server
    :return: True if the EC2 instance is scaled appropriately, False otherwise
    """
    instances = get_ec2('saints-xctf-server-prod-asg')
    return len(instances) < 3


def prod_instance_profile_exists() -> bool:
    """
    Prove that the instance profile exists for the prod EC2 web server
    :return: True if the instance profile exists, False otherwise
    """
    return validate_instance_profile('s3-access-role', is_prod=True)


def prod_launch_config_valid() -> bool:
    """
    Ensure that the Launch Configuration for a SaintsXCTF web server in production is valid
    :return: True if its valid, False otherwise
    """
    instance = get_ec2('saints-xctf-server-prod-asg')[0]
    security_group = instance.security_groups[0]

    lcs = autoscaling.describe_launch_configurations(
        LaunchConfigurationNames=['saints-xctf-server-prod-lc'],
        MaxRecords=1
    )

    launch_config = lcs.get('LaunchConfigurations')[0]

    return all([
        launch_config.get('InstanceType') == 't2.micro',
        launch_config.get('KeyName') == 'saints-xctf-key',
        len(launch_config.get('SecurityGroups')) == 1,
        launch_config.get('SecurityGroups')[0] == security_group.get('GroupId'),
        launch_config.get('IamInstanceProfile') == 'saints-xctf-prod-instance-profile'
    ])


def prod_launch_config_sg_valid():
    """
    Ensure that the security group attached to the launch configuration is as expected
    :return: True if its as expected, False otherwise
    """
    lcs = autoscaling.describe_launch_configurations(
        LaunchConfigurationNames=['saints-xctf-server-prod-lc'],
        MaxRecords=1
    )

    launch_config = lcs.get('LaunchConfigurations')[0]
    security_group_id = launch_config.get('SecurityGroups')[0]

    security_group = ec2.describe_security_groups(GroupIds=[security_group_id]).get('SecurityGroups')[0]

    return all([
        security_group.get('GroupName') == 'saints-xctf-prod-server-lc-security-group',
        validate_launch_config_sg_rules(security_group.get('IpPermissions'), security_group.get('IpPermissionsEgress'))
    ])


def prod_autoscaling_group_valid() -> bool:
    """
    Ensure that the AutoScaling Group for a SaintsXCTF web server in production is valid
    :return: True if its valid, False otherwise
    """
    return validate_autoscaling_group(is_prod=True)


def prod_autoscaling_schedules_unset() -> bool:
    """
    Make sure there are no autoscaling schedules in production (the ASG should always be up)
    :return: True if there are no schedules, False otherwise
    """
    schedules = autoscaling.describe_scheduled_actions(AutoScalingGroupName='saints-xctf-server-prod-asg')
    return len(schedules.get('ScheduledUpdateGroupActions')) == 0


def prod_load_balancer_running():
    """
    Prove that the application load balancer in production is running
    :return: True if its running, False otherwise
    """
    return validate_load_balancer(is_prod=True)


def prod_load_balancer_sg_valid():
    """
    Ensure that the security group attached to the load balancer is as expected
    :return: True if its as expected, False otherwise
    """
    response = ec2.describe_security_groups(GroupNames=['saints-xctf-prod-server-elb-security-group'])
    security_group = response.get('SecurityGroups')[0]

    return all([
        security_group.get('GroupName') == 'saints-xctf-prod-server-elb-security-group',
        validate_launch_config_sg_rules(security_group.get('IpPermissions'), security_group.get('IpPermissionsEgress'))
    ])


"""
Tests for the development environment
"""


def dev_instance_running() -> bool:
    """
    Validate that the EC2 instance(s) holding the development web server are running
    :return: True if the EC2 instance(s) are running, False otherwise
    """
    instances = get_ec2('saints-xctf-server-dev-asg')
    return len(instances) > 0


def dev_instance_not_overscaled() -> bool:
    """
    Ensure that there aren't too many EC2 instances running for the development web server
    :return: True if the EC2 instance is scaled appropriately, False otherwise
    """
    instances = get_ec2('saints-xctf-server-dev-asg')
    return len(instances) < 3


def dev_instance_profile_exists() -> bool:
    """
    Prove that the instance profile exists for the dev EC2 web server
    :return: True if the instance profile exists, False otherwise
    """
    return validate_instance_profile('s3-access-role', is_prod=False)


def dev_launch_config_valid() -> bool:
    """
    Ensure that the Launch Configuration for a SaintsXCTF web server in development is valid
    :return: True if its valid, False otherwise
    """
    instance = get_ec2('saints-xctf-server-dev-asg')[0]
    security_group = instance.security_groups[0]

    lcs = autoscaling.describe_launch_configurations(
        LaunchConfigurationNames=['saints-xctf-server-dev-lc'],
        MaxRecords=1
    )

    launch_config = lcs.get('LaunchConfigurations')[0]

    return all([
        launch_config.get('InstanceType') == 't2.micro',
        launch_config.get('KeyName') == 'saints-xctf-key',
        len(launch_config.get('SecurityGroups')) == 1,
        launch_config.get('SecurityGroups')[0] == security_group.get('GroupId'),
        launch_config.get('IamInstanceProfile') == 'saints-xctf-dev-instance-profile'
    ])


def dev_autoscaling_group_valid() -> bool:
    """
    Ensure that the AutoScaling Group for a SaintsXCTF web server in development is valid
    :return: True if its valid, False otherwise
    """
    return validate_autoscaling_group(is_prod=False)


def dev_autoscaling_schedules_set() -> bool:
    """
    Make sure there are the expected autoscaling schedules in development (the ASG should be down in non-work hours)
    :return: True if there are the expected schedules, False otherwise
    """
    return all([
        validate_autoscaling_schedule('saints-xctf-server-online-weekday-morning', recurrence='30 11 * * 1-5',
                                      max_size=1, min_size=1, desired_size=1),
        validate_autoscaling_schedule('saints-xctf-server-offline-weekday-morning', recurrence='30 13 * * 1-5',
                                      max_size=0, min_size=0, desired_size=0),
        validate_autoscaling_schedule('saints-xctf-server-online-weekday-afternoon', recurrence='30 22 * * 1-5',
                                      max_size=1, min_size=1, desired_size=1),
        validate_autoscaling_schedule('saints-xctf-server-offline-weekday-night', recurrence='30 3 * * 2-6',
                                      max_size=0, min_size=0, desired_size=0),
        validate_autoscaling_schedule('saints-xctf-server-online-weekend', recurrence='30 11 * * 0,6',
                                      max_size=1, min_size=1, desired_size=1),
        validate_autoscaling_schedule('saints-xctf-server-offline-weekend', recurrence='30 3 * * 0,1',
                                      max_size=0, min_size=0, desired_size=0)
    ])


def dev_load_balancer_running():
    """
    Prove that the application load balancer in development is running
    :return: True if its running, False otherwise
    """
    return validate_load_balancer(is_prod=False)


"""
Helper functions to use for retrieving EC2 information
"""


def get_ec2(name: str) -> list:
    """
    Get a list of running EC2 instances with a given name
    :param name: The name of EC2 instances to retrieve
    :return: A list of EC2 instances
    """
    ec2_resource = boto3.resource('ec2')
    filters = [
        {
            'Name': 'tag:Name',
            'Values': [name]
        },
        {
            'Name': 'instance-state-name',
            'Values': ['running']
        }
    ]

    return list(ec2_resource.instances.filter(Filters=filters).all())


def validate_instance_profile(role_name: str, is_prod: bool = True):
    """
    Validate that the instance profile for an EC2 instance contains the expected role
    :param role_name: Role expected on the EC2 instance
    :param is_prod: Whether the EC2 instance is in production environment or not
    :return: True if the instance profile role is as expected, False otherwise
    """
    if is_prod:
        env = "prod"
    else:
        env = "dev"

    # First get the instance profile resource name from the ec2 instance
    instances = get_ec2(f'saints-xctf-server-{env}-asg')
    instance_profile_arn = instances[0].iam_instance_profile.get('Arn')

    # Second get the instance profile from IAM
    instance_profile = iam.get_instance_profile(InstanceProfileName=f'saints-xctf-{env}-instance-profile')
    instance_profile = instance_profile.get('InstanceProfile')

    # Third get the RDS access IAM Role resource name from IAM
    role = iam.get_role(RoleName=role_name)
    role_arn = role.get('Role').get('Arn')

    return all([
        instance_profile_arn == instance_profile.get('Arn'),
        role_arn == instance_profile.get('Roles')[0].get('Arn')
    ])


def validate_autoscaling_group(is_prod: bool = True) -> bool:
    """
    Ensure that the AutoScaling Group for a SaintsXCTF web server in a given environment is valid
    :param is_prod: Whether the EC2 instance is in production environment or not
    :return: True if its valid, False otherwise
    """
    if is_prod:
        env = "prod"
    else:
        env = "dev"

    asgs = autoscaling.describe_auto_scaling_groups(
        AutoScalingGroupNames=[f'saints-xctf-server-{env}-asg'],
        MaxRecords=1
    )

    asg = asgs.get('AutoScalingGroups')[0]

    return all([
        asg.get('LaunchConfigurationName') == f'saints-xctf-server-{env}-lc',
        asg.get('MinSize') == 1,
        asg.get('MaxSize') == 1,
        asg.get('DesiredCapacity') == 1,
        len(asg.get('Instances')) == 1,
        asg.get('Instances')[0].get('LifecycleState') == 'InService',
        asg.get('Instances')[0].get('HealthStatus') == 'Healthy'
    ])


def validate_autoscaling_schedule(name: str, recurrence: str = '', max_size: int = 0,
                                  min_size: int = 0, desired_size: int = 0) -> bool:
    """
    Make sure an autoscaling schedule exists as expected
    :param name: The name of the autoscaling schedule
    :param recurrence: When this schedule recurs
    :param max_size: maximum number of instances in the asg
    :param min_size: minimum number of instances in the asg
    :param desired_size: desired number of instances in the asg
    :return: True if the schedule exists as expected, False otherwise
    """
    response = autoscaling.describe_scheduled_actions(
        AutoScalingGroupName='saints-xctf-server-prod-asg',
        ScheduledActionNames=[name],
        MaxRecords=1
    )

    schedule = response.get('ScheduledUpdateGroupActions')[0]

    return all([
        schedule.get('Recurrence') == recurrence,
        schedule.get('MinSize') == min_size,
        schedule.get('MaxSize') == max_size,
        schedule.get('Recurrence') == desired_size
    ])


def validate_load_balancer(is_prod: bool = True) -> bool:
    """
    Prove that an application load balancer is running by checking its target groups
    :param is_prod: Whether the load balancer is in production environment or not
    :return: True if its running, False otherwise
    """
    if is_prod:
        env = "prod"
    else:
        env = "dev"

    response = autoscaling.describe_load_balancer_target_groups(
        AutoScalingGroupName=f'saints-xctf-server-{env}-asg'
    )

    load_balancers = response.get('LoadBalancerTargetGroups')

    return all([
        len(load_balancers) == 2,
        load_balancers[0].get('State') == 'InService',
        'targetgroup/saints-xctf-lb-target-http' in load_balancers[0].get('LoadBalancerTargetGroupARN'),
        load_balancers[1].get('State') == 'InService',
        'targetgroup/saints-xctf-lb-target' in load_balancers[1].get('LoadBalancerTargetGroupARN'),
    ])


def validate_load_balancer_sg_rules(ingress: list, egress: list, is_prod: bool = True) -> bool:
    if is_prod:
        env = "prod"
    else:
        env = "dev"

    response = ec2.describe_security_groups(GroupNames=[f'saints-xctf-database-security-{env}'])
    database_sg = response.get('SecurityGroups')[0]

    ingress_80 = validate_sg_rule_cidr(ingress[0], 'tcp', 80, 80, '0.0.0.0/0')
    ingress_443 = validate_sg_rule_cidr(ingress[2], 'tcp', 443, 443, '0.0.0.0/0')
    ingress_22 = validate_sg_rule_cidr(ingress[1], 'tcp', 22, 22, '69.124.72.192/32')

    egress_80 = validate_sg_rule_cidr(egress[0], 'tcp', 80, 80, '0.0.0.0/0')
    egress_25 = validate_sg_rule_cidr(egress[1], 'tcp', 25, 25, '0.0.0.0/0')
    egress_3306 = validate_sg_rule_source(egress[2], 'tcp', 3306, 3306, database_sg.get('GroupId'))
    egress_443 = validate_sg_rule_cidr(egress[3], 'tcp', 443, 443, '0.0.0.0/0')

    return all([
        len(ingress) == 3,
        ingress_80,
        ingress_443,
        ingress_22,
        len(egress) == 4,
        egress_80,
        egress_25,
        egress_3306,
        egress_443
    ])


def validate_launch_config_sg_rules(ingress: list, egress: list, is_prod: bool = True) -> bool:
    if is_prod:
        env = "prod"
    else:
        env = "dev"

    response = ec2.describe_security_groups(GroupNames=[f'saints-xctf-database-security-{env}'])
    database_sg = response.get('SecurityGroups')[0]

    return all([
        len(ingress) == 3,
        len(egress) == 5
    ])


def validate_sg_rule_cidr(rule: dict, protocol: str, from_port: int, to_port: int, cidr: str) -> bool:
    """
    Determine if a security group rule which opens connections
    from (ingress) or to (egress) a CIDR block exists as expected.
    :param rule: A dictionary containing security group rule information
    :param protocol: Which protocol the rule enables connections for
    :param from_port: Which source port the rule enables connections for
    :param to_port: Which destination port the rule enables connections for
    :param cidr: The ingress or egress CIDR block
    :return: True if the security group rule exists as expected, False otherwise
    """
    return all([
        rule.get('IpProtocol') == protocol,
        rule.get('FromPort') == from_port,
        rule.get('ToPort') == to_port,
        rule.get('IpRanges')[0].get('CidrIp') == cidr
    ])


def validate_sg_rule_source(rule: dict, protocol: str, from_port: int, to_port: int, source_sg: str) -> bool:
    """
    Determine if a security group rule which opens connections
    from a different source security group exists as expected.
    :param rule: A dictionary containing security group rule information
    :param protocol: Which protocol the rule enables connections for
    :param from_port: Which source port the rule enables connections for
    :param to_port: Which destination port the rule enables connections for
    :param source_sg: The destination security group identifier
    :return: True if the security group rule exists as expected, False otherwise
    """
    return all([
        rule.get('IpProtocol') == protocol,
        rule.get('FromPort') == from_port,
        rule.get('ToPort') == to_port,
        rule.get('UserIdGroupPairs')[0].get('GroupId') == source_sg
    ])


print(prod_launch_config_sg_valid())