from django.contrib import admin
from .models import User, Challenge, Attempt, TestCase, AttemptedCase
from .consumer import consumer

admin.site.register(User)
admin.site.register(Challenge)
admin.site.register(Attempt)
admin.site.register(TestCase)
admin.site.register(AttemptedCase)
