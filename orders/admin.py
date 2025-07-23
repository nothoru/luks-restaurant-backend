# backend/orders/admin.py
from django.contrib import admin
from .models import Orders, OrderItems

class OrderItemInline(admin.TabularInline):
    model = OrderItems
    extra = 0 
    readonly_fields = ('variation', 'quantity', 'price_at_order') 

@admin.register(Orders)
class OrderAdmin(admin.ModelAdmin):
    list_display = ('order_number', 'status', 'order_type', 'total_amount', 'created_at')
    list_filter = ('status', 'order_type', 'created_at')
    inlines = [OrderItemInline]
    readonly_fields = ('created_at', 'updated_at', 'order_number') 