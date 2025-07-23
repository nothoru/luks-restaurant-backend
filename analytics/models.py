# backend/analytics/models.py
from django.db import models

class Analytics(models.Model):

    RECOMMENDATION_STATUS_CHOICES = [
        ('pending', 'Pending Review'),
        ('implemented', 'Implemented'),
        ('dismissed', 'Dismissed'),
    ]
    
    report_type = models.CharField(max_length=10, db_index=True) 
    
    start_date = models.DateField()
    end_date = models.DateField()
    
    total_sales_revenue = models.DecimalField(max_digits=12, decimal_places=2, default=0.00)
    total_order_count = models.IntegerField(default=0)
    
    online_order_count = models.IntegerField(default=0)
    walkin_order_count = models.IntegerField(default=0)
    
    avg_items_per_order = models.FloatField(default=0.0)
    
    dish_performance = models.JSONField(default=list) 
    avg_hourly_orders = models.JSONField(default=list) 
    
    recommendation = models.TextField(blank=True, null=True)
    recommendation_status = models.CharField(max_length=20, choices=RECOMMENDATION_STATUS_CHOICES, default='pending')
    recommendation_updated_at = models.DateTimeField(null=True, blank=True)
    
    generated_at = models.DateTimeField(auto_now_add=True)

    is_viewed = models.BooleanField(default=False)


    class Meta:
        unique_together = ('report_type', 'start_date', 'end_date')
        ordering = ['-start_date']

    def __str__(self):
        return f"{self.report_type.title()} report for {self.start_date} to {self.end_date}"    