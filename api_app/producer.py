import json
import os

from kafka import KafkaProducer

job_init_topic = os.getenv('KAFKA_JOB_INIT_TOPIC')
producer = KafkaProducer(
    bootstrap_servers=os.getenv('KAFKA_BOOTSTRAP_SERVERS'),
    client_id=os.getenv('KAFKA_CLIENT_ID') or 'backend-api',
    value_serializer=lambda v: json.dumps(v).encode('utf-8')
)


def publish_job(attempt, challenge):
    producer.send(job_init_topic, {
        "attempt_id": attempt['id'],
        "user_id": attempt['user_id'],
        "challenge_id": attempt['challenge_id'],
        "query": attempt['query'],
        "init": challenge.init
    })
