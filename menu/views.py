# backend/menu/views.py
from rest_framework import generics, status, serializers
from .models import MenuItems, Categories, Variations
from .serializers import MenuItemSerializer, CategorySerializer, VariationSerializer 
from rest_framework.response import Response
from rest_framework.permissions import IsAuthenticated
from users.permissions import IsStaffUser 
from django.db import transaction
import json 
from backend.pagination import StandardResultsSetPagination
from django.db.models import Q, Exists, OuterRef
from orders.models import OrderItems 

class MenuItemListView(generics.ListAPIView):
    queryset = MenuItems.objects.filter(is_available=True).prefetch_related('variations')
    serializer_class = MenuItemSerializer

    def get_serializer_context(self):
        context = super().get_serializer_context()
        context['filter_available'] = True 
        return context

class CategoryListView(generics.ListAPIView):
    queryset = Categories.objects.all().order_by('name') 
    serializer_class = CategorySerializer

class AdminMenuItemListView(generics.ListCreateAPIView):
    serializer_class = MenuItemSerializer
    permission_classes = [IsAuthenticated, IsStaffUser]
    pagination_class = StandardResultsSetPagination

    def get_queryset(self):
        queryset = MenuItems.objects.select_related('category').prefetch_related('variations').order_by('category__name', 'name')
        
        status_filter = self.request.query_params.get('status', 'active')

        if status_filter == 'active':
            return queryset.filter(is_available=True)
        
        elif status_filter == 'outofstock':
            has_stock = Variations.objects.filter(menu_item=OuterRef('pk'), stock_level__gt=0, is_available=True)
            return queryset.filter(is_available=True).annotate(has_stock=Exists(has_stock)).filter(has_stock=False)

        elif status_filter == 'archived':
            return queryset.filter(is_available=False)
            
        return queryset

    @transaction.atomic
    def create(self, request, *args, **kwargs):
        serializer = self.get_serializer(data=request.data)
        serializer.is_valid(raise_exception=True)
        
        variations_json_str = request.data.get('variations_data', '[]')
        try:
            variations_data = json.loads(variations_json_str)
        except json.JSONDecodeError:
            return Response({'variations_data': 'Invalid JSON format.'}, status=status.HTTP_400_BAD_REQUEST)

        variation_serializer = VariationSerializer(data=variations_data, many=True)
        if not variation_serializer.is_valid():
            return Response(variation_serializer.errors, status=status.HTTP_400_BAD_REQUEST)

        self.perform_create(serializer, variation_serializer.validated_data)
        
        headers = self.get_success_headers(serializer.data)
        return Response(serializer.data, status=status.HTTP_201_CREATED, headers=headers)

    def perform_create(self, serializer, validated_variations):
        menu_item = serializer.save()
        for variation_data in validated_variations:
            Variations.objects.create(menu_item=menu_item, **variation_data)


class AdminMenuItemDetailView(generics.RetrieveUpdateDestroyAPIView):
    queryset = MenuItems.objects.all()
    serializer_class = MenuItemSerializer
    permission_classes = [IsAuthenticated, IsStaffUser]
    lookup_field = 'id'

    @transaction.atomic 
    def update(self, request, *args, **kwargs):
        menu_item = self.get_object()
        item_serializer = self.get_serializer(menu_item, data=request.data, partial=True)
        item_serializer.is_valid(raise_exception=True)
        item_serializer.save()

        if 'variations' in request.data:
            variations_data = json.loads(request.data.get('variations'))
            
           
            for variation_data in variations_data:
                variation_id = variation_data.get('id')
                if variation_id: 
                    try:
                        variation_instance = Variations.objects.get(id=variation_id, menu_item=menu_item)
                        variation_serializer = VariationSerializer(variation_instance, data=variation_data, partial=True)
                        variation_serializer.is_valid(raise_exception=True)
                        variation_serializer.save()
                    except Variations.DoesNotExist:
                        pass
                else:
                    variation_serializer = VariationSerializer(data=variation_data)
                    variation_serializer.is_valid(raise_exception=True)
                    variation_serializer.save(menu_item=menu_item)

        return Response(self.get_serializer(menu_item).data)

    def partial_update(self, request, *args, **kwargs):
        return self.update(request, *args, **kwargs)

    def destroy(self, request, *args, **kwargs):
        menu_item = self.get_object()
        menu_item.is_available = False
        menu_item.save()
        menu_item.variations.update(is_available=False)
        return Response(status=status.HTTP_204_NO_CONTENT)


class AdminVariationDetailView(generics.DestroyAPIView):
    permission_classes = [IsAuthenticated, IsStaffUser]
    queryset = Variations.objects.all()
    lookup_field = 'id'

    def destroy(self, request, *args, **kwargs):
        variation = self.get_object()

        if OrderItems.objects.filter(variation=variation).exists():
            return Response(
                {"error": "Cannot delete: This variation is part of past sales records. To hide it, please set its stock to 0 instead."},
                status=status.HTTP_400_BAD_REQUEST
            )
        
        variation.delete()
        return Response(status=status.HTTP_204_NO_CONTENT)


class AdminCategoryListView(generics.ListCreateAPIView):
    queryset = Categories.objects.all().order_by('name')
    serializer_class = CategorySerializer
    permission_classes = [IsAuthenticated, IsStaffUser]

class AdminCategoryDetailView(generics.RetrieveUpdateDestroyAPIView):
    queryset = Categories.objects.all()
    serializer_class = CategorySerializer
    permission_classes = [IsAuthenticated, IsStaffUser]
    lookup_field = 'id'

    def destroy(self, request, *args, **kwargs):
        category = self.get_object()
        if category.menu_items.exists():
            return Response(
                {'error': 'Cannot delete category because it is being used by one or more menu items.'},
                status=status.HTTP_400_BAD_REQUEST
            )
        return super().destroy(request, *args, **kwargs)