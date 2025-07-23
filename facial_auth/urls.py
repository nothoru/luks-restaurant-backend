# facial_auth/urls.py
from django.urls import path
from . import views

urlpatterns = [
    path("upload_face/", views.upload_face),
    path("verify_face/", views.verify_face),
    path("delete_face/", views.delete_face),
]