# backend/analytics/serializers.py
from rest_framework import serializers
from .models import Analytics

class AnalyticsSerializer(serializers.ModelSerializer):
    recommendation_status_display = serializers.CharField(source='get_recommendation_status_display', read_only=True)
    class Meta:
        model = Analytics
        fields = ['id', 'report_type', 'start_date', 'end_date', 'total_sales_revenue', 
                  'total_order_count', 'online_order_count', 'walkin_order_count', 
                  'avg_items_per_order', 'dish_performance', 'avg_hourly_orders', 
                  'recommendation', 'recommendation_status', 'recommendation_status_display',  'is_viewed',
                  'generated_at']