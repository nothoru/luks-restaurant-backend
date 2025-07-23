from django.core.management.base import BaseCommand
from django.utils import timezone
from datetime import timedelta
from orders.models import Orders

class Command(BaseCommand):
    help = 'Finds and cancels pending orders that are older than one hour.'

    def handle(self, *args, **options):
        one_hour_ago = timezone.now() - timedelta(hours=1)
        
        orders_to_cancel = Orders.objects.filter(
            status='pending',
            created_at__lt=one_hour_ago
        )

        count = orders_to_cancel.count()
        
        if count > 0:
            orders_to_cancel.update(status='cancelled')
            
            self.stdout.write(self.style.SUCCESS(f'Successfully cancelled {count} old pending orders.'))
        else:
            self.stdout.write(self.style.SUCCESS('No old pending orders to cancel.'))