# backend/orders/management/commands/seed_data.py

import random
from datetime import timedelta, date
from django.core.management.base import BaseCommand
from django.utils import timezone
from django.db import transaction
import uuid

from users.models import User
from menu.models import Variations
from orders.models import Orders, OrderItems

class Command(BaseCommand):
    help = 'Seeds the database with a large amount of realistic order data for one year.'

    @transaction.atomic
    def handle(self, *args, **options):
        self.stdout.write("Starting database seeding process...")

        customers = list(User.objects.filter(role='customer'))
        staff_members = list(User.objects.filter(role__in=['staff', 'admin']))
        variations = list(Variations.objects.filter(is_available=True))

        if not customers:
            self.stdout.write(self.style.ERROR("No customers found. Please create customer users first."))
            return
        if not variations:
            self.stdout.write(self.style.ERROR("No menu variations found. Please create menu items and variations first."))
            return
        if not staff_members:
            self.stdout.write(self.style.WARNING("No staff members found. Walk-in orders will not be assigned a processor."))

        end_date = date(2025, 7, 16)
        start_date = date(2024, 7, 16)
        delta = end_date - start_date

        for i in range(delta.days + 1):
            current_date = start_date + timedelta(days=i)
            
            if current_date.weekday() == 6 and random.random() > 0.1: 
                continue

            self.stdout.write(f"Seeding data for {current_date}...")

            num_orders_today = random.randint(20, 100) 
            
            for _ in range(num_orders_today):
                order_type = random.choice(['pre-selection', 'walk-in'])
                customer = random.choice(customers) if order_type == 'pre-selection' else None
                staff = random.choice(staff_members) if order_type == 'walk-in' and staff_members else None
                
                order_hour = random.randint(8, 22)
                order_minute = random.randint(0, 59)
                order_second = random.randint(0, 59)
                order_time = timezone.datetime(
                    current_date.year, current_date.month, current_date.day,
                    order_hour, order_minute, order_second
                )
                aware_order_time = timezone.make_aware(order_time)

                order = Orders.objects.create(
                    user=customer,
                    processed_by_staff=staff,
                    order_number=f"SEED#{str(uuid.uuid4().hex[:8]).upper()}",
                    status='completed', 
                    order_type=order_type,
                    dining_method=random.choice(['dine-in', 'take-out']),
                    total_amount=0, 
                    created_at=aware_order_time,
                    processed_at=aware_order_time + timedelta(minutes=random.randint(5, 30))
                )

                num_items_in_order = random.randint(1, 5)
                order_total = 0
                
                for _ in range(num_items_in_order):
                    variation = random.choice(variations)
                    quantity = random.randint(1, 3)
                    price = variation.price
                    
                    OrderItems.objects.create(
                        order=order,
                        variation=variation,
                        quantity=quantity,
                        price_at_order=price
                    )
                    order_total += price * quantity
                
                order.total_amount = order_total
                order.save()

        self.stdout.write(self.style.SUCCESS('Successfully seeded the database with one year of order data.'))