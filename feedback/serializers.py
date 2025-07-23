# feedback/serializers.py
from rest_framework import serializers
from .models import Feedback
from users.serializers import UserProfileSerializer 

class FeedbackCreateSerializer(serializers.ModelSerializer):
    class Meta:
        model = Feedback
        fields = ['comment'] 

class FeedbackListSerializer(serializers.ModelSerializer):
    user = UserProfileSerializer(read_only=True) 

    class Meta:
        model = Feedback
        fields = ['id', 'user', 'comment', 'sentiment_label', 'created_at']