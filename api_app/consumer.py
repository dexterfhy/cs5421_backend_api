import json
import os
import threading
from datetime import datetime

from django.core.exceptions import ObjectDoesNotExist
from kafka import KafkaConsumer

from api_app.models import AttemptedCase, Challenge
from api_app.serializers import AttemptedCaseSerializer, ChallengeSerializer, TestCaseSerializer

job_init_completion_topic = os.getenv('KAFKA_JOB_INIT_COMPLETION_TOPIC')
job_attempt_completion_topic = os.getenv('KAFKA_JOB_ATTEMPT_COMPLETION_TOPIC')
consumer = KafkaConsumer(
    job_init_completion_topic,
    job_attempt_completion_topic,
    bootstrap_servers=os.getenv('KAFKA_BOOTSTRAP_SERVERS'),
    client_id=os.getenv('KAFKA_CLIENT_ID') or 'backend-api',
    group_id=os.getenv('KAFKA_CONSUMER_GROUP_ID') or 'backend-api-consumer',
    value_deserializer=lambda m: json.loads(m.decode('utf-8'))
)


def handle_job_completion_events():
    for msg in consumer:
        print("Processing job completion event {0}".format(msg))
        if job_init_completion_topic == msg.topic:
            process_job_init_completion(msg)
        elif job_attempt_completion_topic == msg.topic:
            process_job_attempt_completion(msg)


def process_job_init_completion(msg):
    try:
        challenge = Challenge.objects.get(id=msg.value['challenge_id'])

        challenge_data = dict({
            'init_errors': msg.value['error'] or 'Unknown error'
        }) if 'status' in msg.value and msg.value['status'] == 'FAILED' \
            else dict({
            'init_at': datetime.now(),
            'expected_result': msg.value['expected_result'] if 'expected_result' in msg.value else '{}'
        })
        challenge_serializer = ChallengeSerializer(challenge, data=challenge_data, partial=True)

        if challenge_serializer.is_valid():
            challenge_serializer.save()
        else:
            print("Invalid fields for updating challenge {0} with job completion event {1}".format(challenge, msg))

        for test_case in TestCaseSerializer.objects.filter(challenge_id=challenge.id):
            test_case_data = dict({
                'expected_result': msg.value['expected_result'] if 'expected_result' in msg.value else '{}'
            })
            test_case_serializer = TestCaseSerializer(test_case, data=test_case_data, partial=True)

            if test_case_serializer.is_valid():
                test_case_serializer.save()
            else:
                print("Invalid fields for updating test case {0} with job completion event {1}".format(test_case, msg))
    except ObjectDoesNotExist:
        print("Unable to update challenge or test case with job completion event {0}".format(msg))
    except Exception as e:
        print("Unknown error: {}".format(e))


def process_job_attempt_completion(msg):
    try:
        if msg.value['test_case_id']:
            attempted_case = AttemptedCase.objects.get(attempt_id=msg.value['attempt_id'],
                                                       test_case_id=msg.value['test_case_id'])

            update_attempted_case(msg, attempted_case)
        else:
            attempted_cases = AttemptedCase.objects.filter(attempt_id=msg.value['attempt_id'])

            for attempted_case in attempted_cases:
                update_attempted_case(msg, attempted_case)
    except ObjectDoesNotExist:
        print("Unable to update attempt with job completion event {0}".format(msg))
    except Exception as e:
        print("Unknown error: {}".format(e))


def update_attempted_case(msg, attempted_case):
    status = msg.value['status'] if 'status' in msg.value else 'PENDING'
    execution_ms = msg.value['execution_ms'] if 'execution_ms' in msg.value else 0
    if 'CORRECT' == status:
        test_case = TestCaseSerializer.objects.get(id=msg.value['test_case_id'])
        actual_result = test_case.expected_result
    else:
        actual_result = msg.value['actual_result'] if 'actual_result' in msg.value else '{}'
    data = dict({
        'status': status,
        'execution_ms': execution_ms,
        'actual_result': actual_result
    })
    attempted_case_serializer = AttemptedCaseSerializer(attempted_case, data=data, partial=True)
    if attempted_case_serializer.is_valid():
        attempted_case_serializer.save()
    else:
        print("Invalid fields for updating attempt with job completion event {0}".format(msg))


consumer_thread = threading.Thread(target=handle_job_completion_events)
consumer_thread.start()
