import uuid
from kubernetes import client, config


def launch_task(repo_url: str, steps: list[str]) -> None:
    config.load_incluster_config()
    job_name = f"task-{uuid.uuid4().hex[:8]}"

    container = client.V1Container(
        name="sandbox",
        image="sandbox:latest",
        command=["/bin/bash", "-c", " && ".join(steps)],
    )

    template = client.V1PodTemplateSpec(
        metadata=client.V1ObjectMeta(labels={"job": job_name}),
        spec=client.V1PodSpec(containers=[container], restart_policy="Never"),
    )

    job_spec = client.V1JobSpec(template=template, backoff_limit=1)
    job = client.V1Job(metadata=client.V1ObjectMeta(name=job_name), spec=job_spec)

    api = client.BatchV1Api()
    api.create_namespaced_job(namespace="default", body=job)
    print(f"[k8s] launched job {job_name} for repo {repo_url}")
