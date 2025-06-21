import json
import os
import pika


def send_task(description: str, repo_url: str) -> None:
    """Publish a task to the RabbitMQ queue."""
    host = os.environ.get("RABBITMQ_HOST", "rabbitmq")
    connection = pika.BlockingConnection(pika.ConnectionParameters(host=host))
    channel = connection.channel()
    channel.queue_declare(queue="tasks")
    task = {"description": description, "repo_url": repo_url}
    channel.basic_publish(exchange="", routing_key="tasks", body=json.dumps(task))
    connection.close()
