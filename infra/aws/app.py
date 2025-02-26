#!/usr/bin/env python3
import os

import aws_cdk as cdk
from aws_cdk import Stack
from aws_cdk import aws_ec2 as ec2
from constructs import Construct

PREFIX = "ossci-playground-"
N_K8S_NODES = 4


class OssciPlaygroundStack(Stack):

    def __init__(self, scope: Construct, construct_id: str, **kwargs) -> None:
        super().__init__(scope, construct_id, **kwargs)

        ### Configure VPC ###
        vpc = ec2.Vpc.from_lookup(self, f"{PREFIX}vpc", is_default=True)

        ### Configure EC2 Instances ###
        # Creating 3 EC2 instances:
        # - 1 "admin" node (for running Ansible playbooks, Github Actions, etc.)
        # - 4 K8s nodes

        # base config
        base_ec2_kwargs = {
            "vpc": vpc,
            "machine_image": ec2.MachineImage.generic_linux(
                {"us-east-2": "ami-09fe94c6418a9de7b"}
            ),
            "key_pair": ec2.KeyPair.from_key_pair_name(
                self, f"{PREFIX}keypair", f"{PREFIX}keypair"
            ),
        }

        # config specific to admin node
        admin_node_security_group = ec2.SecurityGroup(
            self,
            f"{PREFIX}admin-node-sg",
            vpc=vpc,
            description="allow SSH",
            allow_all_outbound=True,
        )
        admin_node_security_group.add_ingress_rule(
            ec2.Peer.any_ipv4(), ec2.Port.tcp(22), "required for SSH"
        )

        admin_node_user_data = ec2.UserData.for_linux()
        admin_node_user_data.add_commands(
            # install Docker
            "apt-get update -y",
            "apt-get install -y docker.io",
            "systemctl enable docker",
            # configure Docker
            "systemctl start docker",
            "usermod -aG docker ubuntu",
            # install kubectl
            'curl -LO "https://dl.k8s.io/release/v1.32.3/bin/linux/amd64/kubectl"',
            "install -o root -g root -m 0755 kubectl /usr/local/bin/kubectl",
        )

        admin_node_ec2_kwargs = {
            **base_ec2_kwargs,
            "security_group": admin_node_security_group,
            "instance_type": ec2.InstanceType("t2.micro"),
            "user_data": admin_node_user_data,
        }

        # config specific to K8s nodes
        k8s_node_security_group = ec2.SecurityGroup(
            self,
            f"{PREFIX}k8s-node-sg",
            vpc=vpc,
            description="allow SSH",
            allow_all_outbound=True,
        )
        k8s_node_security_group.add_ingress_rule(
            ec2.Peer.any_ipv4(), ec2.Port.tcp(22), "required for SSH"
        )
        k8s_node_security_group.add_ingress_rule(
            ec2.Peer.any_ipv4(),
            ec2.Port.tcp(6443),
            "required for Kubernetes API server on control planes",
        )
        k8s_node_security_group.add_ingress_rule(
            ec2.Peer.any_ipv4(),
            ec2.Port.tcp_range(2379, 2380),
            "required for etcd server client API on control planes",
        )
        k8s_node_security_group.add_ingress_rule(
            ec2.Peer.any_ipv4(),
            ec2.Port.tcp(10250),
            "required for Kubelet API on control planes & workers",
        )
        k8s_node_security_group.add_ingress_rule(
            ec2.Peer.any_ipv4(),
            ec2.Port.tcp(10259),
            "required for kube-scheduler on control planes",
        )
        k8s_node_security_group.add_ingress_rule(
            ec2.Peer.any_ipv4(),
            ec2.Port.tcp(10257),
            "required for kube-controller-manager on control planes",
        )
        k8s_node_security_group.add_ingress_rule(
            ec2.Peer.any_ipv4(),
            ec2.Port.tcp(10256),
            "required for kube-proxy on workers",
        )
        k8s_node_security_group.add_ingress_rule(
            ec2.Peer.any_ipv4(),
            ec2.Port.tcp_range(30000, 32767),
            "required for NodePort Services on workers",
        )

        k8s_node_ec2_kwargs = {
            **base_ec2_kwargs,
            "security_group": k8s_node_security_group,
            "instance_type": ec2.InstanceType("t2.medium"),
        }

        # provision admin node
        ec2.Instance(self, f"{PREFIX}admin-node", **admin_node_ec2_kwargs)

        # provision K8s nodes
        for id in [f"{PREFIX}k8s-node-{i}" for i in range(1, N_K8S_NODES + 1)]:
            ec2.Instance(self, id, **k8s_node_ec2_kwargs)


app = cdk.App()
OssciPlaygroundStack(
    app,
    f"{PREFIX}stack",
    env=cdk.Environment(
        account=os.environ["CDK_ACCOUNT"],
        region=os.environ["CDK_REGION"],
    ),
)

app.synth()
