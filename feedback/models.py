# feedback/models.py
from django.db import models
from users.models import User

class Feedback(models.Model):
 
    user = models.ForeignKey(User, on_delete=models.CASCADE, related_name='feedbacks')
    
    comment = models.TextField(max_length=250) 
    
    sentiment_label = models.CharField(max_length=10, blank=True, null=True) 
    sentiment_score = models.FloatField(blank=True, null=True)
    
    created_at = models.DateTimeField(auto_now_add=True)

    def __str__(self):
        return f"Feedback from {self.user.email} on {self.created_at.strftime('%Y-%m-%d')}"

    class Meta:
        ordering = ['-created_at'] 