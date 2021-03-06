from rest_framework import serializers

from .models import User, Challenge, Attempt, TestCase, AttemptedCase


class UserSerializer(serializers.ModelSerializer):
    id = serializers.IntegerField(required=False)
    email = serializers.EmailField()
    full_name = serializers.CharField(max_length=255)
    role = serializers.CharField(max_length=50)
    unsafe_password = serializers.CharField(max_length=255)
    created_at = serializers.DateTimeField(required=False)

    class Meta:
        model = User
        fields = ('__all__')


class ChallengeSerializer(serializers.ModelSerializer):
    id = serializers.IntegerField(required=False)
    created_user_id = serializers.IntegerField()
    name = serializers.CharField(max_length=255)
    description = serializers.CharField(required=False)
    type = serializers.CharField(max_length=2)
    init = serializers.CharField()
    init_at = serializers.DateTimeField(required=False)
    init_errors = serializers.CharField(required=False)
    expires_at = serializers.DateTimeField()
    solution = serializers.CharField()
    times_to_run = serializers.IntegerField()
    created_at = serializers.DateTimeField(required=False)

    class Meta:
        model = Challenge
        fields = ('__all__')


class TestCaseSerializer(serializers.ModelSerializer):
    id = serializers.IntegerField(required=False)
    challenge_id = serializers.IntegerField()
    data = serializers.CharField()
    is_visible = serializers.BooleanField()
    created_at = serializers.DateTimeField(required=False)

    class Meta:
        model = TestCase
        fields = ('__all__')


class AttemptSerializer(serializers.ModelSerializer):
    id = serializers.IntegerField(required=False)
    user_id = serializers.IntegerField()
    challenge_id = serializers.IntegerField()
    query = serializers.CharField()
    created_at = serializers.DateTimeField(required=False)

    class Meta:
        model = Attempt
        fields = ('__all__')


class AttemptedCaseSerializer(serializers.ModelSerializer):
    id = serializers.IntegerField(required=False)
    attempt_id = serializers.IntegerField()
    test_case_id = serializers.IntegerField()
    execution_ms = serializers.FloatField(required=False)
    expected_result = serializers.CharField(required=False)
    actual_result = serializers.CharField(required=False)
    created_at = serializers.DateTimeField(required=False)

    class Meta:
        model = AttemptedCase
        fields = ('__all__')
