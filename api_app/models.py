from django.db import models
from django.utils.translation import gettext_lazy as _


class User(models.Model):
    id = models.BigAutoField(primary_key=True)
    email = models.CharField(max_length=255)
    full_name = models.CharField(max_length=255)
    unsafe_password = models.CharField(max_length=255)
    created_at = models.DateTimeField(auto_now_add=True)


class Challenge(models.Model):
    class Type(models.TextChoices):
        FASTEST_EXECUTION = 'FE', _('FASTEST_EXECUTION')
        LONGEST_EXECUTION = 'LE', _('LONGEST_EXECUTION')

    id = models.BigAutoField(primary_key=True)
    name = models.CharField(max_length=255)
    description = models.TextField(null=True)
    type = models.CharField(
        max_length=2,
        choices=Type.choices,
        default=Type.FASTEST_EXECUTION,
    )
    init = models.TextField()
    created_at = models.DateTimeField(auto_now_add=True)


class Attempt(models.Model):
    class Status(models.TextChoices):
        PENDING = 'PENDING', _('PENDING')
        COMPLETED = 'COMPLETED', _('COMPLETED')
        FAILED = 'FAILED', _('FAILED')
        TIMED_OUT = 'TIMED_OUT', _('TIMED_OUT')

    id = models.BigAutoField(primary_key=True)
    user_id = models.PositiveIntegerField()
    challenge_id = models.PositiveIntegerField()
    status = models.CharField(
        max_length=50,
        choices=Status.choices,
        default=Status.PENDING,
    )
    query = models.TextField()
    execution_ms = models.PositiveIntegerField(null=True)
    score = models.PositiveIntegerField(null=True)
    created_at = models.DateTimeField(auto_now_add=True)
