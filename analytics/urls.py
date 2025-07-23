# backend/analytics/urls.py
from django.urls import path
from .views import AnalyticsDataView, PerformanceReportView, RecommendationView

urlpatterns = [
    path('', AnalyticsDataView.as_view(), name='analytics-data'),
    path('performance-report/', PerformanceReportView.as_view(), name='performance-report'),
    path('recommendation/', RecommendationView.as_view(), name='analytics-recommendation'),

]