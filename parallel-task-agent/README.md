# Parallel Task Coding Agent

This directory contains an autonomous coding agent designed to execute coding tasks in isolated Kubernetes sandboxes.

## Features

- **Ephemeral Kubernetes Sandboxes** – each task runs in its own container launched via `k8s_launcher.py`.
- **Task Queue** – RabbitMQ limits each user to 3–5 concurrent tasks.
- **Secure Execution** – sandboxes use `nsjail` and Kubernetes NetworkPolicies to restrict outbound traffic to GitHub, PyPI and NPM.
- **GPT‑5 Mini Integration** – `llm_integration.py` decomposes tasks and generates code.
- **Diff Validation** – `validate_diff.py` enforces code style with ESLint, Black and Pylint before tests run.
- **Secrets Handling** – HashiCorp Vault provides short‑lived credentials.
- **Audit Logging** – all actions are recorded to immutable CloudWatch Trails.

## Setup

1. **Provision Infrastructure**
   ```bash
   cd infra
   terraform init
   terraform apply
   ```
   This creates a Kubernetes cluster, RabbitMQ instance, Vault server and storage bucket.

2. **Build Sandbox Image**
   ```bash
   docker build -t sandbox:latest sandbox-image
   ```

3. **Install Helm Charts**
   ```bash
   helm install monitoring ./helm -f helm/monitoring_values.yaml
   ```

4. **Run the Agent**
   ```bash
   python agent/main.py
   ```

## Development

- The sandbox image pins Ubuntu 22.04, `git`, Python 3.11 and `nodejs`.
- Terraform files are examples; adjust for your cloud provider.
- Ensure Vault policies restrict secrets to a 15‑minute TTL.

## Testing

The validator runs Black, Pylint and ESLint in a temporary environment. Automated tests should be added to each repository so the agent can execute them before opening a pull request.

