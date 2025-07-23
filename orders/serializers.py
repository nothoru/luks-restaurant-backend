# orders/serializers.py
from rest_framework import serializers
from .models import Orders, OrderItems
from menu.models import Variations
from users.serializers import UserProfileSerializer

class CartItemSerializer(serializers.Serializer):
    variation_id = serializers.IntegerField()
    quantity = serializers.IntegerField(min_value=1)

class OrderCreateSerializer(serializers.ModelSerializer):
    items = CartItemSerializer(many=True, write_only=True) 
    class Meta:
        model = Orders
        fields = ['dining_method', 'items'] 

class OrderVariationDetailSerializer(serializers.ModelSerializer):
    menu_item_name = serializers.CharField(source='menu_item.name', read_only=True)
    menu_item_image = serializers.ImageField(source='menu_item.image', read_only=True)

    class Meta:
        model = Variations 
        fields = ['id', 'size_name', 'price', 'menu_item_name', 'menu_item_image']


class OrderItemDetailSerializer(serializers.ModelSerializer):
    variation = OrderVariationDetailSerializer(read_only=True)
    
    class Meta:
        model = OrderItems
        fields = ['id', 'variation', 'quantity', 'price_at_order']


class OrderListSerializer(serializers.ModelSerializer):
    order_items = OrderItemDetailSerializer(many=True, read_only=True) 
    user = UserProfileSerializer(read_only=True) 
    processed_by_staff = UserProfileSerializer(read_only=True)


    class Meta:
        model = Orders
        fields = [
            'id', 
            'order_number', 
            'user',
            'processed_by_staff',
            'total_amount', 
            'status', 
            'dining_method', 
            'created_at',
            'order_items',
            'table_number',   
            'amount_paid',     
            'change_given',   
        ]

class SalesReportSerializer(serializers.ModelSerializer):
    user = UserProfileSerializer(read_only=True)
    processed_by_staff = UserProfileSerializer(read_only=True)
    
    type = serializers.SerializerMethodField()
    items_summary = serializers.SerializerMethodField()

    class Meta:
        model = Orders
        fields = [
            'id', 'order_number', 'processed_at', 'type', 'user', 
            'processed_by_staff', 'items_summary', 'total_amount'
        ]

    def get_type(self, obj):
        order_type = obj.get_order_type_display()
        dining_method = obj.get_dining_method_display()
        return f"{order_type} ({dining_method})"

    def get_items_summary(self, obj):
        items = [
            f"{item.variation.menu_item.name} ({item.variation.size_name}) x{item.quantity}"
            for item in obj.order_items.all()
        ]
        return ", ".join(items)