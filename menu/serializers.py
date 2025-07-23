# menu/serializers.py
from rest_framework import serializers
from .models import MenuItems, Variations, Categories
from django.db import transaction
import json

class VariationSerializer(serializers.ModelSerializer):
    class Meta:
        model = Variations
        fields = ['id', 'size_name', 'price', 'stock_level', 'is_available']
        read_only_fields = ['id']

class CategorySerializer(serializers.ModelSerializer):
    class Meta:
        model = Categories
        fields = ['id', 'name']

class MenuItemSerializer(serializers.ModelSerializer):
    variations = VariationSerializer(many=True, read_only=True)
    category = CategorySerializer(read_only=True)
    is_fully_out_of_stock = serializers.BooleanField(read_only=True)
    
    
    category_id = serializers.IntegerField(write_only=True)

    class Meta:
        model = MenuItems
        fields = [
            'id', 'name', 'image', 'is_available',
            'category', 'category_id', 
            'variations', 
            'is_fully_out_of_stock' 
        ]
        