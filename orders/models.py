# orders/models.py
from django.db import models
from users.models import User 
from menu.models import Variations 
from django.utils import timezone 


class Orders(models.Model):
    STATUS_CHOICES = [
        ('pending', 'Pending'),  # Online order waiting for payment
        ('processing', 'Processing'), # Paid, kitchen is preparing
        ('ready_to_serve', 'Ready to Serve'), # Food is ready, waiting for pickup
        ('completed', 'Completed'), # Customer has picked up the food 
        ('cancelled', 'Cancelled'), # Order cancelled
    ]
    
    ORDER_TYPE_CHOICES = [('pre-selection', 'Pre-Selection'), ('walk-in', 'Walk-In')]
    DINING_METHOD_CHOICES = [('dine-in', 'Dine-In'), ('take-out', 'Take-Out')]

    user = models.ForeignKey(User, on_delete=models.SET_NULL, null=True, blank=True)
    order_number = models.CharField(max_length=50, unique=True)
    processed_by_staff = models.ForeignKey(User, on_delete=models.SET_NULL, null=True, blank=True, related_name='processed_orders')
    total_amount = models.DecimalField(max_digits=10, decimal_places=2)
    status = models.CharField(max_length=20, choices=STATUS_CHOICES, default='pending')
    order_type = models.CharField(max_length=20, choices=ORDER_TYPE_CHOICES, default='pre-selection')
    dining_method = models.CharField(max_length=20, choices=DINING_METHOD_CHOICES)
    
    amount_paid = models.DecimalField(max_digits=10, decimal_places=2, null=True, blank=True)
    change_given = models.DecimalField(max_digits=10, decimal_places=2, null=True, blank=True)
    

    table_number = models.CharField(max_length=10, null=True, blank=True)

    processed_at = models.DateTimeField(null=True, blank=True, db_index=True)

    created_at = models.DateTimeField(default=timezone.now)
    updated_at = models.DateTimeField(auto_now=True)
    
    def __str__(self):
        return self.order_number

class OrderItems(models.Model):
    order = models.ForeignKey(Orders, on_delete=models.CASCADE, related_name='order_items')
    variation = models.ForeignKey(Variations, on_delete=models.PROTECT) 
    quantity = models.PositiveIntegerField(default=1)
    price_at_order = models.DecimalField(max_digits=10, decimal_places=2) 
    
    def __str__(self):
        return f"{self.quantity} of {self.variation.menu_item.name} ({self.variation.size_name})"