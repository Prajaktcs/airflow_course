import pulumi_aws as aws


vpc = aws.ec2.Vpc(
    "mwaa-vpc",
    cidr_block="10.0.0.0/16",
    enable_dns_hostnames=True,
    enable_dns_support=True,
)

internet_gateway = aws.ec2.InternetGateway(
    "internet-gateway", vpc_id=vpc.id, tags={"Name": "InternetGateway"}
)

# Create a public subnet in the VPC
public_subnet = aws.ec2.Subnet(
    "public-subnet",
    vpc_id=vpc.id,
    cidr_block="10.0.1.0/24",
    availability_zone="us-west-2a",
    map_public_ip_on_launch=True,  # Ensures instances in this subnet get a public IP
    tags={"Name": "PublicSubnet"},
)

public_subnet_2 = aws.ec2.Subnet(
    "public-subnet-2",
    vpc_id=vpc.id,
    cidr_block="10.0.2.0/24",
    availability_zone="us-west-2b",
    map_public_ip_on_launch=True,  # Ensures instances in this subnet get a public IP
    tags={"Name": "PublicSubnet"},
)

# Create a route table for the public subnet
public_route_table = aws.ec2.RouteTable(
    "public-route-table",
    vpc_id=vpc.id,
    routes=[{"cidr_block": "0.0.0.0/0", "gateway_id": internet_gateway.id}],
    tags={"Name": "PublicRouteTable"},
)

# Associate the public subnet with the public route table
public_route_table_assoc = aws.ec2.RouteTableAssociation(
    "public-subnet-route-association",
    subnet_id=public_subnet.id,
    route_table_id=public_route_table.id,
)

public_route_table_assoc_2 = aws.ec2.RouteTableAssociation(
    "public-subnet-2-route-association",
    subnet_id=public_subnet_2.id,
    route_table_id=public_route_table.id,
)


private_subnet_1 = aws.ec2.Subnet(
    "private-subnet-1",
    vpc_id=vpc.id,
    cidr_block="10.0.3.0/24",
    availability_zone="us-west-2a",
)

private_subnet_2 = aws.ec2.Subnet(
    "private-subnet-2",
    vpc_id=vpc.id,
    cidr_block="10.0.4.0/24",
    availability_zone="us-west-2b",
)

nat_eip_a = aws.ec2.Eip("nat-eip-a", vpc=True)
nat_eip_b = aws.ec2.Eip("nat-eip-b", vpc=True)

nat_gateway_a = aws.ec2.NatGateway(
    "gateway-a", subnet_id=public_subnet.id, allocation_id=nat_eip_a.id
)

nat_gateway_b = aws.ec2.NatGateway(
    "gateway-b", subnet_id=public_subnet_2.id, allocation_id=nat_eip_b.id
)


# Create a route table for the private subnets
private_route_table_a = aws.ec2.RouteTable(
    "private-route-table-a",
    vpc_id=vpc.id,
    routes=[{"cidr_block": "0.0.0.0/0", "nat_gateway_id": nat_gateway_a.id}],
    tags={"Name": "PrivateRouteTable"},
)

private_route_table_b = aws.ec2.RouteTable(
    "private-route-table-b",
    vpc_id=vpc.id,
    routes=[{"cidr_block": "0.0.0.0/0", "nat_gateway_id": nat_gateway_b.id}],
    tags={"Name": "PrivateRouteTable"},
)

# Associate the route table with the private subnets
private_subnet_1_route_assoc = aws.ec2.RouteTableAssociation(
    "private-subnet-1-route-association",
    subnet_id=private_subnet_1.id,
    route_table_id=private_route_table_a.id,
)

private_subnet_2_route_assoc = aws.ec2.RouteTableAssociation(
    "private-subnet-2-route-association",
    subnet_id=private_subnet_2.id,
    route_table_id=private_route_table_b.id,
)


security_group = aws.ec2.SecurityGroup(
    "airflow-security-group",
    vpc_id=vpc.id,
    description="Allow inbound traffic for Airflow environment",
    ingress=[
        # Allow inbound traffic on port 80 (HTTP)
        {
            "protocol": "tcp",
            "from_port": 80,
            "to_port": 80,
            "cidr_blocks": ["49.36.40.176/32"],
        },
        # Allow inbound traffic on port 443 (HTTPS)
        {
            "protocol": "tcp",
            "from_port": 443,
            "to_port": 443,
            "cidr_blocks": ["49.36.40.176/32"],
        },
        # Allow access to postgres
        {"protocol": "tcp", "from_port": 5432, "to_port": 5432, "self": True},
        {"protocol": "all", "from_port": 0, "to_port": 0, "self": True},
    ],
    egress=[
        # Allow all outbound traffic
        {
            "protocol": "-1",
            "from_port": 0,
            "to_port": 0,
            "cidr_blocks": ["0.0.0.0/0"],
        }
    ],
)
