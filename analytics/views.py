# backend/analytics/views.py
from rest_framework.views import APIView
from rest_framework.response import Response
from rest_framework.permissions import IsAuthenticated
from users.permissions import IsAdminUser
from .models import Analytics
from .serializers import AnalyticsSerializer

from django.utils.dateparse import parse_date
from django.db.models import Sum, Count, Avg, F
from orders.models import Orders, OrderItems
from django.utils import timezone
from datetime import timedelta

class AnalyticsDataView(APIView):
    permission_classes = [IsAuthenticated, IsAdminUser]

    def get(self, request):
        report_type = request.query_params.get('report_type', 'daily')
        
        if report_type not in ['daily', 'weekly', 'monthly', 'yearly']:
            return Response({"error": "Invalid report_type specified."}, status=400)

        analytics_record = Analytics.objects.filter(report_type=report_type).order_by('-start_date').first()

        if not analytics_record:
            return Response({"message": "No analytics data found for the selected period."}, status=404)

        serializer = AnalyticsSerializer(analytics_record)
        return Response(serializer.data)
    

class PerformanceReportView(APIView):
    permission_classes = [IsAuthenticated, IsAdminUser]

    def get(self, request):
        end_date_str = request.query_params.get('end_date', timezone.now().isoformat())
        start_date_str = request.query_params.get('start_date', (timezone.now() - timedelta(days=30)).isoformat())

        start_date = parse_date(start_date_str)
        end_date = parse_date(end_date_str)

        if not start_date or not end_date:
            return Response({"error": "Invalid date format. Use YYYY-MM-DD."}, status=400)

        orders_in_period = Orders.objects.filter(
            status='completed',
            processed_at__date__gte=start_date,
            processed_at__date__lte=end_date
        )

        summary = orders_in_period.aggregate(
            total_revenue=Sum('total_amount'),
            total_orders=Count('id'),
        )
        
        order_items_in_period = OrderItems.objects.filter(order__in=orders_in_period)
        total_items_sold = order_items_in_period.aggregate(total=Sum('quantity'))['total'] or 0
        
        summary['total_items_sold'] = total_items_sold
        summary['average_order_value'] = (summary['total_revenue'] / summary['total_orders']) if summary['total_orders'] else 0

        item_performance = (
            order_items_in_period
            .values(
                'variation__menu_item__name', 
                'variation__size_name'
            )
            .annotate(
                item_name=F('variation__menu_item__name'),
                variation_name=F('variation__size_name'),
                units_sold=Sum('quantity'),
                total_revenue=Sum(F('quantity') * F('price_at_order')),
                average_price=Avg('price_at_order')
            )
            .values(
                'item_name', 'variation_name', 'units_sold', 
                'total_revenue', 'average_price'
            )
            .order_by('-total_revenue')
        )

        response_data = {
            'summary': summary,
            'item_performance': list(item_performance)
        }

        return Response(response_data)
    
class RecommendationView(APIView):
    permission_classes = [IsAuthenticated, IsAdminUser]

    def get(self, request):
        """Fetches the latest weekly recommendation."""
        latest_recommendation = Analytics.objects.filter(
            report_type='weekly', 
            recommendation__isnull=False
        ).order_by('-start_date').first()

        if not latest_recommendation:
            return Response({"message": "No recommendations available yet."}, status=status.HTTP_404_NOT_FOUND)
        
        if not latest_recommendation.is_viewed:
            latest_recommendation.is_viewed = True
            latest_recommendation.save()
        
        serializer = AnalyticsSerializer(latest_recommendation)
        return Response(serializer.data)

    def patch(self, request):
        """Updates the status of a recommendation."""
        report_id = request.data.get('report_id')
        new_status = request.data.get('status')
        
        if not report_id or not new_status:
            return Response({"error": "report_id and status are required."}, status=status.HTTP_400_BAD_REQUEST)
        
        valid_statuses = [choice[0] for choice in Analytics.RECOMMENDATION_STATUS_CHOICES]
        if new_status not in valid_statuses:
            return Response({"error": "Invalid status provided."}, status=status.HTTP_400_BAD_REQUEST)

        try:
            report = Analytics.objects.get(id=report_id)
            report.recommendation_status = new_status
            report.recommendation_updated_at = timezone.now()
            report.save()
            return Response({"success": "Status updated successfully."})
        except Analytics.DoesNotExist:
            return Response({"error": "Report not found."}, status=status.HTTP_404_NOT_FOUND)
