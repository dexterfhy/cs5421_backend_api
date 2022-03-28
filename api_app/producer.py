import json
import os

from kafka import KafkaProducer

from api_app.models import Challenge

job_init_topic = os.getenv('KAFKA_JOB_INIT_TOPIC')
job_attempt_fast_topic = os.getenv('KAFKA_JOB_ATTEMPT_FAST_TOPIC')
job_attempt_slow_topic = os.getenv('KAFKA_JOB_ATTEMPT_SLOW_TOPIC')
producer = KafkaProducer(
    bootstrap_servers=os.getenv('KAFKA_BOOTSTRAP_SERVERS'),
    client_id=os.getenv('KAFKA_CLIENT_ID') or 'backend-api',
    key_serializer=lambda k: k.encode('utf-8'),
    value_serializer=lambda v: json.dumps(v).encode('utf-8'),
)


def publish_job_init(challenge, test_cases):
    producer.send(
        job_init_topic,
        {
            "challenge_id": challenge.id,
            "challenge_name": challenge.name,
            "init": challenge.init,
            "expires_at": challenge.expires_at.isoformat(),
            "solution": challenge.solution,
            "times_to_run": challenge.times_to_run,
            "test_cases": list(map(lambda test_case: {
                "id": test_case.id,
                "data": test_case.data
            }, test_cases)),
        },
        key=str(challenge.id)
    )


def publish_job_update(challenge):
    producer.send(
        job_init_topic,
        {
            "challenge_id": challenge.id,
            "expires_at": challenge.expires_at.isoformat(),
            "times_to_run": challenge.times_to_run,
        },
        key=str(challenge.id)
    )


def publish_job_attempt(attempt, challenge):
    producer.send(
        job_attempt_slow_topic if challenge.type == Challenge.Type.SLOWEST_EXECUTION else job_attempt_fast_topic,
        {
            "attempt_id": attempt['id'],
            "user_id": attempt['user_id'],
            "challenge_id": challenge.id,
            "challenge_name": challenge.name,
            "query": attempt['query']
        },
        key=str(challenge.id)
    )
