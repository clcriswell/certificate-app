import json
import os
import pika
from k8s_launcher import launch_task
from llm_integration import decompose_task

MAX_CONCURRENT = 5


def main() -> None:
    connection = pika.BlockingConnection(pika.ConnectionParameters(host=os.environ.get("RABBITMQ_HOST", "rabbitmq")))
    channel = connection.channel()
    channel.queue_declare(queue="tasks")

    def callback(ch, method, properties, body):
        task = json.loads(body)
        print(f"[agent] received task {task.get('id')}")
        steps = decompose_task(task.get("description", ""))
        launch_task(task.get("repo_url"), steps)

    channel.basic_qos(prefetch_count=MAX_CONCURRENT)
    channel.basic_consume(queue="tasks", on_message_callback=callback, auto_ack=True)
    print("[agent] waiting for tasks")
    channel.start_consuming()


if __name__ == "__main__":
    main()
