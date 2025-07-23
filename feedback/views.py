# feedback/views.py
from rest_framework import generics
from rest_framework.permissions import IsAuthenticated
from .models import Feedback
from .serializers import FeedbackCreateSerializer, FeedbackListSerializer
from users.permissions import IsAdminUser 

from .utils import analyze_sentiment

from backend.pagination import StandardResultsSetPagination



class FeedbackCreateView(generics.CreateAPIView):
    queryset = Feedback.objects.all()
    serializer_class = FeedbackCreateSerializer
    permission_classes = [IsAuthenticated] 

    def perform_create(self, serializer):
        comment_text = serializer.validated_data.get('comment', '')

        sentiment_label, sentiment_score = analyze_sentiment(comment_text)

        serializer.save(
            user=self.request.user,
            sentiment_label=sentiment_label,
            sentiment_score=sentiment_score
        )

class AdminFeedbackListView(generics.ListAPIView):
    queryset = Feedback.objects.all()
    serializer_class = FeedbackListSerializer
    permission_classes = [IsAuthenticated, IsAdminUser] 

    pagination_class = StandardResultsSetPagination
