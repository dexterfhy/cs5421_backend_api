import json
import os
import threading

from django.core.exceptions import ObjectDoesNotExist
from kafka import KafkaConsumer

from api_app.models import AttemptedCase
from api_app.serializers import AttemptedCaseSerializer

job_completion_topic = os.getenv('KAFKA_JOB_COMPLETION_TOPIC')
consumer = KafkaConsumer(
    job_completion_topic,
    bootstrap_servers=os.getenv('KAFKA_BOOTSTRAP_SERVERS'),
    client_id=os.getenv('KAFKA_CLIENT_ID') or 'backend-api',
    group_id=os.getenv('KAFKA_CONSUMER_GROUP_ID') or 'backend-api-consumer',
    value_deserializer=lambda m: json.loads(m.decode('utf-8'))
)


def handle_job_completion_events():
    for msg in consumer:
        print("Processing job completion event {0}".format(msg))
        try:
            attempted_case = AttemptedCase.objects.get(attempt_id=msg.value['attempt_id'], test_case_id=msg.value['test_case_id'])

            data = dict({
                'status': msg.value['status'] if 'status' in msg.value else 'PENDING',
                'execution_ms': msg.value['execution_ms'] if 'execution_ms' in msg.value else 0,
                'score': msg.value['score'] if 'score' in msg.value else 0
            })
            serializer = AttemptedCaseSerializer(attempted_case, data=data, partial=True)

            if serializer.is_valid():
                serializer.save()
            else:
                print("Invalid fields for updating attempt with job completion event {0}".format(msg))
        except ObjectDoesNotExist:
            print("Unable to update attempt with job completion event {0}".format(msg))


consumer_thread = threading.Thread(target=handle_job_completion_events)
consumer_thread.start()
