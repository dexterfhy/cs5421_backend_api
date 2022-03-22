from django.core.exceptions import ObjectDoesNotExist
from django.http import HttpResponse
from django.views.decorators.http import require_http_methods
from rest_framework import status
from rest_framework.decorators import api_view
from rest_framework.response import Response

from .models import User, Attempt, Challenge, TestCase
from .producer import publish_job
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
            return Response({"status": "error", "message": "User email already exists"}, status=status.HTTP_400_BAD_REQUEST)
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

    return Response({"status": "error", "message": "Email or password not specified"}, status=status.HTTP_400_BAD_REQUEST)


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
            return Response({"status": "success", "data": serializer.data}, status=status.HTTP_200_OK)
        except ObjectDoesNotExist:
            return Response({"status": "error", "message": "Attempt not found"}, status=status.HTTP_404_NOT_FOUND)

    return Response({"status": "error", "message": "User ID or attempt ID not specified"}, status=status.HTTP_400_BAD_REQUEST)


@api_view(["GET", "POST"])
def fetch_challenges_or_create_new(request):
    if request.method == 'GET':
        challenges = list(map(lambda x: build_challenge(ChallengeSerializer(x).data), list(Challenge.objects.all())))
        return Response({"status": "success", "data": challenges}, status=status.HTTP_200_OK)
    else:
        challenge_serializer = ChallengeSerializer(data=dict(
            {
                "created_user_id": request.data["user_id"],
                "name": request.data["name"],
                "description": request.data["description"],
                "type": request.data["type"],
                "init": request.data["init"],
                "solution": request.data["solution"],
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

            return Response({"status": "success", "data": build_challenge(challenge_serializer.data)}, status=status.HTTP_200_OK)
        else:
            return Response({"status": "error", "message": challenge_serializer.errors}, status=status.HTTP_400_BAD_REQUEST)


@api_view(["GET"])
def get_challenge(request, challenge_id=None):
    if challenge_id:
        try:
            challenge = Challenge.objects.get(id=challenge_id)
            serializer = ChallengeSerializer(challenge)
            return Response({"status": "success", "data": build_challenge(serializer.data)}, status=status.HTTP_200_OK)
        except ObjectDoesNotExist:
            return Response({"status": "error", "message": "Challenge not found"}, status=status.HTTP_404_NOT_FOUND)

    return Response({"status": "error", "message": "Challenge ID not specified"}, status=status.HTTP_400_BAD_REQUEST)


@api_view(["GET"])
def get_challenge_by_user(request, user_id=None):
    if user_id:
        try:
            challenges = list(map(lambda x: build_challenge(ChallengeSerializer(x).data), Challenge.objects.filter(created_user_id=user_id)))
            return Response({"status": "success", "data": challenges}, status=status.HTTP_200_OK)
        except ObjectDoesNotExist:
            return Response({"status": "error", "message": "Challenge not found"}, status=status.HTTP_404_NOT_FOUND)

    return Response({"status": "error", "message": "Challenge ID not specified"}, status=status.HTTP_400_BAD_REQUEST)


@api_view(["POST"])
def attempt_challenge(request):
    user_id = request.data['user_id']
    challenge_id = request.data['challenge_id']

    if user_id and challenge_id:
        try:
            User.objects.get(id=user_id)
            challenge = Challenge.objects.get(id=challenge_id)
            test_cases = TestCase.objects.filter(challenge_id=challenge_id)

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

                publish_job(attempt_serializer.data, challenge, test_cases)
                return Response({"status": "success", "data": attempt_serializer.data}, status=status.HTTP_200_OK)
            else:
                return Response({"status": "error", "message": attempt_serializer.errors}, status=status.HTTP_400_BAD_REQUEST)
        except ObjectDoesNotExist:
            return Response({"status": "error", "message": "User or challenge not found"}, status=status.HTTP_404_NOT_FOUND)

    return Response({"status": "error", "message": "User ID or challenge ID not specified"}, status=status.HTTP_400_BAD_REQUEST)


def build_challenge(challenge_data):
    challenge_data["test_cases"] = list(map(
        lambda x: TestCaseSerializer(x).data,
        list(TestCase.objects.filter(challenge_id=challenge_data["id"]))
    ))
    return challenge_data
