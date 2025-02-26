#!/usr/bin/env python3
import os

import aws_cdk as cdk
from aws_cdk import Stack
from aws_cdk import aws_ec2 as ec2
from constructs import Construct

PREFIX = "kubespray-poc-"
N_K8S_CONTROLPLANE_NODES = 1
N_K8S_WORKER_NODES = 1


class KubesprayPocStack(Stack):

    def __init__(self, scope: Construct, construct_id: str, **kwargs) -> None:
        super().__init__(scope, construct_id, **kwargs)

        ### Configure VPC ###
        vpc = ec2.Vpc.from_lookup(self, f"{PREFIX}vpc", is_default=True)

        ### Configure Security Group ###
        # To keep things simple, no restrictions on SSH ingress/egress for now.
        security_group = ec2.SecurityGroup(
            self,
            f"{PREFIX}sg",
            vpc=vpc,
            description="allow SSH",
            allow_all_outbound=True,
        )
        security_group.add_ingress_rule(
            ec2.Peer.any_ipv4(), ec2.Port.tcp(22), "allow SSH from anywhere"
        )

        ### Configure EC2 Instances ###
        # Creating 3 EC2 instances:
        # - 1 Ansible control node
        # - 2 Kubernetes nodes (1 controlplane & etcd, 1 worker)

        # common config
        ubuntu_2204_ami = ec2.MachineImage.generic_linux(
            {"us-east-2": "ami-09fe94c6418a9de7b"}
        )
        key_pair = ec2.KeyPair.from_key_pair_name(
            self, f"{PREFIX}keypair", f"{PREFIX}keypair"
        )

        # setup specific to Ansible control node
        ansible_controller_instance_type = ec2.InstanceType("t2.micro")
        ansible_controller_user_data = ec2.UserData.for_linux()
        ansible_controller_user_data.add_commands(
            # install Docker
            "apt-get update -y",
            "apt-get install -y docker.io",
            "systemctl enable docker",
            # configure Docker
            "systemctl start docker",
            "usermod -aG docker ubuntu",
        )

        # setup specific to K8s nodes
        k8s_controlplane_instance_type = ec2.InstanceType("t2.medium")
        k8s_worker_instance_type = ec2.InstanceType("t2.small")

        # provision Ansible control node
        ec2.Instance(
            self,
            f"{PREFIX}ansible-controller",
            instance_type=ansible_controller_instance_type,
            machine_image=ubuntu_2204_ami,
            vpc=vpc,
            security_group=security_group,
            key_pair=key_pair,
            user_data=ansible_controller_user_data,
        )

        # provision Kubernetes controlplane/etcd nodes
        for id in [
            f"{PREFIX}controlplane-node{i}"
            for i in range(1, N_K8S_CONTROLPLANE_NODES + 1)
        ]:
            ec2.Instance(
                self,
                id,
                instance_type=k8s_controlplane_instance_type,
                machine_image=ubuntu_2204_ami,
                vpc=vpc,
                security_group=security_group,
                key_pair=key_pair,
            )

        # provision Kubernetes worker nodes
        for id in [f"{PREFIX}worker-node{i}" for i in range(1, N_K8S_WORKER_NODES + 1)]:
            ec2.Instance(
                self,
                id,
                instance_type=k8s_worker_instance_type,
                machine_image=ubuntu_2204_ami,
                vpc=vpc,
                security_group=security_group,
                key_pair=key_pair,
            )


app = cdk.App()
KubesprayPocStack(
    app,
    f"{PREFIX}stack",
    env=cdk.Environment(
        account=os.environ["CDK_ACCOUNT"],
        region=os.environ["CDK_REGION"],
    ),
)

app.synth()
