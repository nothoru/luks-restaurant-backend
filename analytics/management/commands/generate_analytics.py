# backend/analytics/management/commands/generate_analytics.py

from django.core.management.base import BaseCommand
from django.utils import timezone
from django.db.models import Sum, Count, Avg, F, ExpressionWrapper, FloatField, Case, When
from django.db.models.functions import TruncHour, Extract
from datetime import timedelta, date

from orders.models import Orders, OrderItems
from analytics.models import Analytics
from django.utils.timezone import localtime 


class Command(BaseCommand):
    help = 'Generates daily, weekly, and monthly sales analytics reports.'

    def handle(self, *args, **options):
        self.stdout.write("Starting analytics generation...")

        local_now = localtime(timezone.now())
        today = local_now.date()
        
        yesterday = today - timedelta(days=1)
        self.generate_report_for_period('daily', yesterday, yesterday)

        last_week_start = today - timedelta(days=today.weekday() + 7)
        last_week_end = last_week_start + timedelta(days=6)
        self.generate_report_for_period('weekly', last_week_start, last_week_end)

        first_day_of_current_month = today.replace(day=1)
        last_day_of_last_month = first_day_of_current_month - timedelta(days=1)
        first_day_of_last_month = last_day_of_last_month.replace(day=1)
        self.generate_report_for_period('monthly', first_day_of_last_month, last_day_of_last_month)
        
        first_day_of_current_year = today.replace(month=1, day=1)
        last_day_of_last_year = first_day_of_current_year - timedelta(days=1)
        first_day_of_last_year = last_day_of_last_year.replace(month=1, day=1)
        self.generate_report_for_period('yearly', first_day_of_last_year, last_day_of_last_year)

        self.stdout.write(self.style.SUCCESS('Successfully generated all analytics reports.'))

    def generate_report_for_period(self, report_type, start_date, end_date):
        self.stdout.write(f"Generating {report_type} report for {start_date} to {end_date}...")

        num_days_in_period = (end_date - start_date).days + 1

        orders_in_period = Orders.objects.filter(
            status='completed',
            created_at__date__gte=start_date,
            created_at__date__lte=end_date
        )

        if not orders_in_period.exists():
            self.stdout.write(f"No completed orders found for this period. Skipping.")
            Analytics.objects.update_or_create(
                report_type=report_type,
                start_date=start_date,
                end_date=end_date,
                defaults={
                    'total_sales_revenue': 0,
                    'total_order_count': 0,
                    'online_order_count': 0,
                    'walkin_order_count': 0,
                    'avg_items_per_order': 0,
                    'dish_performance': [],
                    'avg_hourly_orders': [],
                }
            )
            return

        total_revenue = orders_in_period.aggregate(total=Sum('total_amount'))['total'] or 0
        total_orders = orders_in_period.count()
        online_orders = orders_in_period.filter(order_type='pre-selection').count()
        walkin_orders = orders_in_period.filter(order_type='walk-in').count()

        total_items_sold = OrderItems.objects.filter(order__in=orders_in_period).aggregate(total=Sum('quantity'))['total'] or 0
        avg_items = total_items_sold / total_orders if total_orders > 0 else 0

        dish_performance = list(OrderItems.objects.filter(order__in=orders_in_period)
            .values('variation__menu_item__name')
            .annotate(dish_name=F('variation__menu_item__name'), sold=Sum('quantity'))
            .order_by('-sold')
            .values('dish_name', 'sold')[:10]
        )

        num_days_in_period = (end_date - start_date).days + 1
        
        hourly_orders_query = (orders_in_period
            .annotate(hour=Extract('created_at', 'hour'))
            .values('hour')
            .annotate(total_orders_in_hour=Count('id'))
            .order_by('hour')
        )

        hourly_map = {item['hour']: item['total_orders_in_hour'] for item in hourly_orders_query}
        formatted_hourly = []
        for h in range(24): 
            total_orders_for_hour = hourly_map.get(h, 0)
            
            if report_type == 'daily':
                value = total_orders_for_hour
            else:
                value = round(total_orders_for_hour / num_days_in_period, 2)
                
            formatted_hourly.append({'hour': h, 'orders': value})

        Analytics.objects.update_or_create(
            report_type=report_type,
            start_date=start_date,
            end_date=end_date,
            defaults={
                'total_sales_revenue': total_revenue,
                'total_order_count': total_orders,
                'online_order_count': online_orders,
                'walkin_order_count': walkin_orders,
                'avg_items_per_order': round(avg_items, 2),
                'dish_performance': dish_performance,
                'avg_hourly_orders': formatted_hourly, 
            }
        )