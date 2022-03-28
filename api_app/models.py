from django.db import models
from django.utils.translation import gettext_lazy as _


class User(models.Model):
    class Role(models.TextChoices):
        PROFESSOR = 'PROF', _('PROFESSOR')
        STUDENT = 'STUD', _('STUDENT')

    id = models.BigAutoField(primary_key=True)
    email = models.CharField(max_length=255)
    full_name = models.CharField(max_length=255)
    role = models.CharField(
        max_length=10,
        choices=Role.choices,
        default=Role.STUDENT,
    )
    unsafe_password = models.CharField(max_length=255)
    created_at = models.DateTimeField(auto_now_add=True)


class Challenge(models.Model):
    class Type(models.TextChoices):
        FASTEST_EXECUTION = 'FE', _('FASTEST_EXECUTION')
        SLOWEST_EXECUTION = 'SE', _('SLOWEST_EXECUTION')

    id = models.BigAutoField(primary_key=True)
    created_user_id = models.PositiveIntegerField()
    name = models.CharField(max_length=255)
    description = models.TextField(null=True)
    type = models.CharField(
        max_length=2,
        choices=Type.choices,
        default=Type.FASTEST_EXECUTION,
    )
    init = models.TextField()
    init_at = models.DateTimeField(null=True)
    init_errors = models.TextField(null=True)
    expires_at = models.DateTimeField()
    solution = models.TextField()
    times_to_run = models.PositiveIntegerField()
    created_at = models.DateTimeField(auto_now_add=True)


class TestCase(models.Model):
    id = models.BigAutoField(primary_key=True)
    challenge_id = models.PositiveIntegerField()
    data = models.TextField()
    is_visible = models.BooleanField()
    created_at = models.DateTimeField(auto_now_add=True)


class Attempt(models.Model):
    id = models.BigAutoField(primary_key=True)
    user_id = models.PositiveIntegerField()
    challenge_id = models.PositiveIntegerField()
    query = models.TextField()
    created_at = models.DateTimeField(auto_now_add=True)


class AttemptedCase(models.Model):
    class Status(models.TextChoices):
        PENDING = 'PENDING', _('PENDING')
        COMPLETED = 'COMPLETED', _('COMPLETED')
        FAILED = 'FAILED', _('FAILED')
        TIMED_OUT = 'TIMED_OUT', _('TIMED_OUT')
        INVALIDATED = 'INVALIDATED', _('INVALIDATED')

    id = models.BigAutoField(primary_key=True)
    attempt_id = models.PositiveIntegerField()
    test_case_id = models.PositiveIntegerField()
    status = models.CharField(
        max_length=50,
        choices=Status.choices,
        default=Status.PENDING,
    )
    execution_ms = models.PositiveIntegerField(null=True)
    expected_result = models.TextField(null=True)
    actual_result = models.TextField(null=True)
    created_at = models.DateTimeField(auto_now_add=True)
