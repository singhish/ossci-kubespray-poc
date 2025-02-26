# IaC scripts for deploying OSSCI Playground infra in AWS

## Overview

We are using [AWS CDK](https://aws.amazon.com/cdk/) to idempotently manage the lifecycles of the AWS resources needed for the OSSCI Playground such as EC2 instances, VPCs, security groups, etc.

## Getting started

1. Ensure [`aws-cli`](https://docs.aws.amazon.com/cli/latest/userguide/getting-started-install.html) and [`aws-cdk`](https://docs.aws.amazon.com/cdk/v2/guide/getting_started.html) are installed and configured in your development environment.

1. After cloning this repo, `cd` into this directory (`./aws/`), set up a Python venv, and activate it:

    ```bash
    python -m venv .venv
    source .venv/bin/activate
    ```

1. Install `requirements.txt` and `requirements-dev.txt` (in a CI scenario, only `requirements.txt` would be needed):

    ```bash
    pip install -r requirements.txt
    pip install -r requirements-dev.txt
    ```

1. Ensure `CDK_ACCOUNT` and `CDK_REGION` have been exported as environment variables:

    ```bash
    export CDK_ACCOUNT=000000000000 # Shark AWS account's ID
    export CDK_REGION=us-east-2     # Shark AWS account's region
    ```

1. Validate that CDK is working properly by ensuring the `kubespray-poc-stack` is up:

    ```bash
    cdk list
    #> kubespray-poc-stack
    ```

1. To be able to SSH into the EC2 instances, ensure you have access to `kubespray-poc-keypair.pem`, and then SSH into one of the instances using its IP address listed on the dashboard, e.g.:

    ```bash
    ssh -i ~/.ssh/kubespray-poc-keypair.pem ubuntu@<IP of EC2 instance>
    ```
