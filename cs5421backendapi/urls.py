"""cs5421backendapi URL Configuration

The `urlpatterns` list routes URLs to views. For more information please see:
    https://docs.djangoproject.com/en/3.2/topics/http/urls/
Examples:
Function views
    1. Add an import:  from my_app import views
    2. Add a URL to urlpatterns:  path('', views.home, name='home')
Class-based views
    1. Add an import:  from other_app.views import Home
    2. Add a URL to urlpatterns:  path('', Home.as_view(), name='home')
Including another URLconf
    1. Import the include() function: from django.urls import include, path
    2. Add a URL to urlpatterns:  path('blog/', include('blog.urls'))
"""
from django.contrib import admin
from django.urls import path
from api_app import views

urlpatterns = [
    path('admin/', admin.site.urls),
    path('', views.healthcheck),
    path('register', views.register),
    path('login', views.login),
    path('users/<int:user_id>', views.get_user),
    path('users/<int:user_id>/attempts/<int:attempt_id>', views.get_challenge_attempt),
    path('challenges', views.fetch_challenges_or_create_new),
    path('challenges/<int:challenge_id>', views.get_challenge),
    path('attempts', views.attempt_challenge)
]
