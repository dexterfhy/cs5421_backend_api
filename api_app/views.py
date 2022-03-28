from django.core.exceptions import ObjectDoesNotExist
from django.http import HttpResponse
from django.views.decorators.http import require_http_methods
from rest_framework import status
from rest_framework.decorators import api_view
from rest_framework.response import Response

from .models import User, Attempt, Challenge, TestCase, AttemptedCase
from .producer import publish_job_init, publish_job_attempt, publish_job_update
from .serializers import UserSerializer, AttemptSerializer, ChallengeSerializer, TestCaseSerializer, \
    AttemptedCaseSerializer


@require_http_methods(["GET"])
def healthcheck(request):
    return HttpResponse(content='Hello, world', status=201)


@api_view(["POST"])
def register(request):
    serializer = UserSerializer(data=request.data)
    if serializer.is_valid():
        try:
            User.objects.get(email=request.data['email'])
            return Response({"status": "error", "message": "User email already exists"},
                            status=status.HTTP_400_BAD_REQUEST)
        except ObjectDoesNotExist:
            serializer.save()
            return Response({"status": "success", "data": serializer.data}, status=status.HTTP_200_OK)
    else:
        return Response({"status": "error", "message": serializer.errors}, status=status.HTTP_400_BAD_REQUEST)


@api_view(["POST"])
def login(request):
    email = request.data['email']
    password = request.data['unsafe_password']

    if email and password:
        try:
            user = User.objects.get(email=email, unsafe_password=password)
            serializer = UserSerializer(user)
            return Response({"status": "success", "data": serializer.data}, status=status.HTTP_200_OK)
        except ObjectDoesNotExist:
            return Response({"status": "error", "message": "User not found"}, status=status.HTTP_404_NOT_FOUND)

    return Response({"status": "error", "message": "Email or password not specified"},
                    status=status.HTTP_400_BAD_REQUEST)


@api_view(["GET"])
def get_user(request, user_id=None):
    if user_id:
        try:
            user = User.objects.get(id=user_id)
            serializer = UserSerializer(user)
            return Response({"status": "success", "data": serializer.data}, status=status.HTTP_200_OK)
        except ObjectDoesNotExist:
            return Response({"status": "error", "message": "User not found"}, status=status.HTTP_404_NOT_FOUND)

    return Response({"status": "error", "message": "User ID not specified"}, status=status.HTTP_400_BAD_REQUEST)


@api_view(["GET"])
def get_challenge_attempt(request, user_id=None, attempt_id=None):
    if user_id and attempt_id:
        try:
            attempt = Attempt.objects.get(user_id=user_id, id=attempt_id)
            serializer = AttemptSerializer(attempt)
            return Response({"status": "success", "data": build_attempt(serializer.data)}, status=status.HTTP_200_OK)
        except ObjectDoesNotExist:
            return Response({"status": "error", "message": "Attempt not found"}, status=status.HTTP_404_NOT_FOUND)

    return Response({"status": "error", "message": "User ID or attempt ID not specified"},
                    status=status.HTTP_400_BAD_REQUEST)


@api_view(["GET", "POST"])
def fetch_challenges_or_create_new(request):
    if request.method == 'GET':
        challenges = list(map(lambda x: build_challenge(ChallengeSerializer(x).data),
                              filter(lambda x: not x["init_errors"],
                                     map(lambda x: ChallengeSerializer(x).data, list(Challenge.objects.all())))))
        return Response({"status": "success", "data": challenges}, status=status.HTTP_200_OK)
    else:
        try:
            if not User.objects.get(id=request.data["user_id"]).role == "PROF":
                return Response({"status": "error", "message": "Only professors may create challenges."},
                                status=status.HTTP_400_BAD_REQUEST)
        except ObjectDoesNotExist:
            return Response({"status": "error", "message": "User not found"}, status=status.HTTP_404_NOT_FOUND)

        challenge_serializer = ChallengeSerializer(data=dict(
            {
                "created_user_id": request.data["user_id"],
                "name": request.data["name"],
                "description": request.data["description"],
                "type": request.data["type"],
                "init": request.data["init"],
                "expires_at": request.data["expires_at"],
                "solution": request.data["solution"],
                "times_to_run": request.data["times_to_run"],
            }
        ))
        if challenge_serializer.is_valid():
            challenge_serializer.save()

            for test_case_request in request.data["test_cases"]:
                test_case_serializer = TestCaseSerializer(data=dict(
                    {
                        "challenge_id": challenge_serializer.data["id"],
                        "data": test_case_request["data"],
                        "is_visible": test_case_request["is_visible"]
                    }
                ))
                if test_case_serializer.is_valid():
                    test_case_serializer.save()

            challenge_id = challenge_serializer.data["id"]
            challenge = Challenge.objects.get(id=challenge_id)
            test_cases = TestCase.objects.filter(challenge_id=challenge_id)

            publish_job_init(challenge, test_cases)
            return Response({"status": "success", "data": build_challenge(challenge_serializer.data)},
                            status=status.HTTP_200_OK)
        else:
            return Response({"status": "error", "message": challenge_serializer.errors},
                            status=status.HTTP_400_BAD_REQUEST)


@api_view(["GET", "PATCH"])
def get_or_update_challenge(request, challenge_id=None):
    if challenge_id:
        try:
            challenge = Challenge.objects.get(id=challenge_id)

            if request.method == 'GET':
                serializer = ChallengeSerializer(challenge)
                return Response({"status": "success", "data": build_top_challenge(serializer.data)}, status=status.HTTP_200_OK)
            else:
                try:
                    if not User.objects.get(id=request.data["user_id"]).role == "PROF":
                        return Response({"status": "error", "message": "Only professors may create challenges."},
                                        status=status.HTTP_400_BAD_REQUEST)
                except ObjectDoesNotExist:
                    return Response({"status": "error", "message": "User not found"}, status=status.HTTP_404_NOT_FOUND)

                data = dict({
                    "description": request.data["description"] or challenge.description,
                    "expires_at": request.data["expires_at"] or challenge.expires_at,
                    "times_to_run": request.data["times_to_run"] or challenge.times_to_run,
                })
                serializer = ChallengeSerializer(challenge, data=data, partial=True)

                if serializer.is_valid():
                    serializer.save()
                    publish_job_update(challenge)
                    return Response({"status": "success", "data": build_challenge(serializer.data)}, status=status.HTTP_200_OK)
                else:
                    return Response({"status": "error", "message": serializer.errors}, status=status.HTTP_404_NOT_FOUND)
        except ObjectDoesNotExist:
            return Response({"status": "error", "message": "Challenge not found"}, status=status.HTTP_404_NOT_FOUND)

    return Response({"status": "error", "message": "Challenge ID not specified"}, status=status.HTTP_400_BAD_REQUEST)


@api_view(["GET"])
def get_challenge_by_user(request, user_id=None):
    if user_id:
        try:
            challenges = list(map(lambda x: build_challenge(ChallengeSerializer(x).data),
                                  Challenge.objects.filter(created_user_id=user_id)))
            return Response({"status": "success", "data": challenges}, status=status.HTTP_200_OK)
        except ObjectDoesNotExist:
            return Response({"status": "error", "message": "Challenge not found"}, status=status.HTTP_404_NOT_FOUND)

    return Response({"status": "error", "message": "User ID not specified"}, status=status.HTTP_400_BAD_REQUEST)


@api_view(["POST"])
def attempt_challenge(request):
    user_id = request.data['user_id']
    challenge_id = request.data['challenge_id']

    if user_id and challenge_id:
        try:
            User.objects.get(id=user_id)
            challenge = Challenge.objects.get(id=challenge_id)
            test_cases = TestCase.objects.filter(challenge_id=challenge_id)

            if not challenge.init_at:
                return Response({"status": "error", "message": "Challenge is not ready yet."},
                                status=status.HTTP_400_BAD_REQUEST)

            attempt_serializer = AttemptSerializer(data=request.data)
            if attempt_serializer.is_valid():
                attempt_serializer.save()

                for test_case in test_cases:
                    attempted_case_serializer = AttemptedCaseSerializer(data=dict(
                        {
                            "attempt_id": attempt_serializer.data["id"],
                            "test_case_id": test_case.id
                        }
                    ))
                    if attempted_case_serializer.is_valid():
                        attempted_case_serializer.save()

                publish_job_attempt(attempt_serializer.data, challenge)
                return Response({"status": "success", "data": attempt_serializer.data}, status=status.HTTP_200_OK)
            else:
                return Response({"status": "error", "message": attempt_serializer.errors},
                                status=status.HTTP_400_BAD_REQUEST)
        except ObjectDoesNotExist:
            return Response({"status": "error", "message": "User or challenge not found"},
                            status=status.HTTP_404_NOT_FOUND)

    return Response({"status": "error", "message": "User ID or challenge ID not specified"},
                    status=status.HTTP_400_BAD_REQUEST)


@api_view(["POST"])
def invalidate_attempt(request, attempt_id=None):
    if attempt_id:
        try:
            for attempted_case in AttemptedCase.objects.filter(attempt_id=attempt_id):
                serializer = AttemptedCaseSerializer(attempted_case, data=dict({'status': 'INVALIDATED'}), partial=True)

                if serializer.is_valid():
                    serializer.save()
                else:
                    print("Unable to invalidate {}".format(attempted_case))

            return Response({"status": "success", "data": "Invalidated attempt {}".format(attempt_id)}, status=status.HTTP_200_OK)
        except ObjectDoesNotExist:
            return Response({"status": "error", "message": "Attempt not found"}, status=status.HTTP_404_NOT_FOUND)

    return Response({"status": "error", "message": "Attempt ID not specified"}, status=status.HTTP_400_BAD_REQUEST)


def build_challenge(challenge_data):
    challenge_data["test_cases"] = list(map(
        lambda x: TestCaseSerializer(x).data,
        list(TestCase.objects.filter(challenge_id=challenge_data["id"]))
    ))
    return challenge_data


def build_top_challenge(challenge_data):
    test_cases = list(TestCase.objects.filter(challenge_id=challenge_data["id"]))

    challenge_data["test_cases"] = list(map(lambda x: TestCaseSerializer(x).data, test_cases))

    hidden_test_case_ids = list(map(lambda x: x.id, filter(lambda x: not x.is_visible, test_cases)))

    challenge_data["top_attempts"] = list(map(build_challenge_attempt, AttemptedCase.objects
                                              .filter(status='COMPLETED', test_case_id__in=hidden_test_case_ids)
                                              .order_by('test_case_id',
                                                        '-execution_ms'
                                                        if challenge_data['type'] == 'SE' else 'execution_ms',
                                                        '-created_at')
                                              .distinct('test_case_id')))

    return challenge_data


def build_attempt(attempt_data):
    attempt_data["attempts"] = list(map(
        lambda x: build_attempted_case(AttemptedCaseSerializer(x).data),
        list(AttemptedCase.objects.filter(attempt_id=attempt_data["id"]))
    ))
    return attempt_data


def build_attempted_case(attempted_case_data):
    is_visible = TestCase.objects.get(id=attempted_case_data["test_case_id"]).is_visible
    attempted_case_data["is_visible"] = is_visible
    if not is_visible:
        attempted_case_data.pop("expected_result", None)
        attempted_case_data.pop("actual_result", None)

    return attempted_case_data


def build_challenge_attempt(attempted_case):
    return dict({
        'test_case_id': attempted_case.test_case_id,
        'user_full_name': User.objects.get(id=Attempt.objects.get(id=attempted_case.attempt_id).user_id).full_name,
        'completion_time_ms': attempted_case.execution_ms,
        'time_of_attempt': attempted_case.created_at
    })
