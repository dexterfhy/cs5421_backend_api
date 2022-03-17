from django.core.exceptions import ObjectDoesNotExist
from django.http import HttpResponse
from django.views.decorators.http import require_http_methods
from rest_framework import status
from rest_framework.decorators import api_view
from rest_framework.response import Response

from .models import User, Attempt, Challenge
from .producer import publish_job
from .serializers import UserSerializer, AttemptSerializer, ChallengeSerializer


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
        challenges = list(map(lambda x: ChallengeSerializer(x).data, list(Challenge.objects.all())))
        return Response({"status": "success", "data": challenges}, status=status.HTTP_200_OK)
    else:
        serializer = ChallengeSerializer(data=request.data)
        if serializer.is_valid():
            serializer.save()
            return Response({"status": "success", "data": serializer.data}, status=status.HTTP_200_OK)
        else:
            return Response({"status": "error", "message": serializer.errors}, status=status.HTTP_400_BAD_REQUEST)


@api_view(["GET"])
def get_challenge(request, challenge_id=None):
    if challenge_id:
        try:
            challenge = Challenge.objects.get(id=challenge_id)
            serializer = ChallengeSerializer(challenge)
            return Response({"status": "success", "data": serializer.data}, status=status.HTTP_200_OK)
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

            serializer = AttemptSerializer(data=request.data)
            if serializer.is_valid():
                serializer.save()
                publish_job(serializer.data, challenge)
                return Response({"status": "success", "data": serializer.data}, status=status.HTTP_200_OK)
            else:
                return Response({"status": "error", "message": serializer.errors}, status=status.HTTP_400_BAD_REQUEST)
        except ObjectDoesNotExist:
            return Response({"status": "error", "message": "User or challenge not found"}, status=status.HTTP_404_NOT_FOUND)

    return Response({"status": "error", "message": "User ID or challenge ID not specified"}, status=status.HTTP_400_BAD_REQUEST)
