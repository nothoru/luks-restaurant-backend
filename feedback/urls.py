# feedback/urls.py
from django.urls import path
from .views import FeedbackCreateView, AdminFeedbackListView

urlpatterns = [
    path('submit/', FeedbackCreateView.as_view(), name='feedback-submit'),
    path('admin/all/', AdminFeedbackListView.as_view(), name='admin-feedback-list'),
]