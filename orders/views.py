# backend/orders/views.py
from rest_framework import generics, status
from rest_framework.response import Response
from rest_framework.permissions import IsAuthenticated
from django.db import transaction
import uuid 
from django.db.models import Q 
from django.utils import timezone
from django.utils.timezone import localtime
from django.utils.dateparse import parse_date
from datetime import datetime, time, timedelta

from .models import Orders, OrderItems
from menu.models import Variations
from .serializers import OrderCreateSerializer, OrderListSerializer , SalesReportSerializer

from rest_framework.views import APIView 
from users.permissions import IsStaffUser 
from backend.pagination import StandardResultsSetPagination 

class OrderCreateView(generics.CreateAPIView):
    serializer_class = OrderCreateSerializer
    permission_classes = [IsAuthenticated] 

    @transaction.atomic 
    def create(self, request, *args, **kwargs):
        serializer = self.get_serializer(data=request.data) 
        serializer.is_valid(raise_exception=True)
        
        cart_items = serializer.validated_data['items']
        dining_method = serializer.validated_data['dining_method']
        
        total_amount = 0
        items_to_create = []
        
        for item_data in cart_items:
            try:
                variation = Variations.objects.get(id=item_data['variation_id'])
                if variation.stock_level < item_data['quantity']:
                    return Response(
                        {'error': f"Not enough stock for {variation.menu_item.name} ({variation.size_name}). Only {variation.stock_level} left."},
                        status=status.HTTP_400_BAD_REQUEST
                    )
                total_amount += variation.price * item_data['quantity']
                items_to_create.append({
                    'variation': variation,
                    'quantity': item_data['quantity'],
                    'price_at_order': variation.price
                })
            except Variations.DoesNotExist:
                return Response({'error': 'Invalid item in cart.'}, status=status.HTTP_400_BAD_REQUEST)

        order = Orders.objects.create(
            user=request.user,
            order_number=f"ORDER#{str(uuid.uuid4().fields[-1])[:8].upper()}", 
            total_amount=total_amount,
            dining_method=dining_method,
            status='pending', 
            order_type='pre-selection'
        )

        order_item_objects = []
        for item_info in items_to_create:
            order_item_objects.append(
                OrderItems(
                    order=order,
                    variation=item_info['variation'],
                    quantity=item_info['quantity'],
                    price_at_order=item_info['price_at_order']
                )
            )
        OrderItems.objects.bulk_create(order_item_objects)
        return Response({'success': 'Order created successfully!', 'order_id': order.id}, status=status.HTTP_201_CREATED)
    
class UserOrderListView(generics.ListAPIView):
    serializer_class = OrderListSerializer
    permission_classes = [IsAuthenticated]
    pagination_class = StandardResultsSetPagination  


    def get_queryset(self):
        return Orders.objects.filter(user=self.request.user).order_by('-created_at')
    
class AdminOrderListView(generics.ListAPIView):
    serializer_class = OrderListSerializer
    permission_classes = [IsAuthenticated, IsStaffUser] 

    def get_queryset(self):
        status_filter = self.request.query_params.get('status', 'pending')
        queryset = Orders.objects.filter(status=status_filter)

        if status_filter == 'completed':
            today = localtime(timezone.now()).date()
            queryset = queryset.filter(updated_at__date=today) 

        search_query = self.request.query_params.get('search', None)
        if search_query:
            queryset = queryset.filter(
                Q(order_number__icontains=search_query) |
                Q(user__first_name__icontains=search_query) |
                Q(user__last_name__icontains=search_query)
            ).distinct()

        if status_filter == 'pending':
            return queryset.order_by('created_at')
        else:
            return queryset.order_by('-updated_at')

class AdminOrderDetailView(generics.UpdateAPIView):
    serializer_class = OrderListSerializer 
    permission_classes = [IsAuthenticated, IsStaffUser]
    queryset = Orders.objects.all()
    lookup_field = 'id'

    @transaction.atomic
    def partial_update(self, request, *args, **kwargs):
        order = self.get_object()
        new_status = request.data.get('status')

        if order.status == 'pending' and new_status == 'processing':
            for item in order.order_items.all():
                variation = item.variation
                if variation.stock_level < item.quantity:
                    return Response(
                        {'error': f"Stock for {variation.menu_item.name} is insufficient."},
                        status=status.HTTP_409_CONFLICT
                    )
                variation.stock_level -= item.quantity
                variation.save()

            order.processed_at = timezone.now()
            order.table_number = request.data.get('table_number', order.table_number)
            order.amount_paid = request.data.get('amount_paid', order.amount_paid)
            order.change_given = request.data.get('change_given', order.change_given)
            order.payment_status = 'paid'

        order.status = new_status
        order.save()

        serializer = self.get_serializer(order)
        return Response(serializer.data)

class POSOrderCreateView(APIView):
    permission_classes = [IsAuthenticated, IsStaffUser]

    @transaction.atomic
    def post(self, request, *args, **kwargs): 
        cart_items = request.data.get('items', [])
        dining_method = request.data.get('dining_method')
        table_number = request.data.get('table_number')
        amount_paid_str = request.data.get('amount_paid')
        change_given_str = request.data.get('change_given')

        if not cart_items:
            return Response({'error': 'Order must contain items.'}, status=status.HTTP_400_BAD_REQUEST)
        if not dining_method:
             return Response({'error': 'Dining method is required.'}, status=status.HTTP_400_BAD_REQUEST)
        
        try:
            amount_paid = float(amount_paid_str) if amount_paid_str else 0.0
            change_given = float(change_given_str) if change_given_str else 0.0
        except (ValueError, TypeError):
            return Response({'error': 'Invalid payment amount provided.'}, status=status.HTTP_400_BAD_REQUEST)

        total_amount = 0
        items_to_process = []
        
        for item_data in cart_items:
            try:
                variation = Variations.objects.get(id=item_data['variation_id'])
                if variation.stock_level < item_data['quantity']:
                    return Response(
                        {'error': f"Not enough stock for {variation.menu_item.name} ({variation.size_name})."},
                        status=status.HTTP_400_BAD_REQUEST
                    )
                item_price = variation.price
                total_amount += item_price * item_data['quantity']
                items_to_process.append({
                    'variation': variation,
                    'quantity': item_data['quantity'],
                    'price_at_order': item_price
                })
            except Variations.DoesNotExist:
                return Response({'error': 'Invalid item ID in order.'}, status=status.HTTP_400_BAD_REQUEST)

        order = Orders.objects.create(
            user=None,
            processed_by_staff=request.user,
            order_number=f"POS#{str(uuid.uuid4().fields[-1])[:8].upper()}", 
            total_amount=total_amount,
            dining_method=dining_method,
            status='processing',
            order_type='walk-in',
            processed_at=timezone.now(),
            table_number=table_number,
            amount_paid=amount_paid,
            change_given=change_given
        )

        order_item_objects = []
        for item_info in items_to_process:
            order_item_objects.append(
                OrderItems(
                    order=order,
                    variation=item_info['variation'],
                    quantity=item_info['quantity'],
                    price_at_order=item_info['price_at_order']
                )
            )
            variation_to_update = item_info['variation']
            variation_to_update.stock_level -= item_info['quantity']
            variation_to_update.save()
            
        OrderItems.objects.bulk_create(order_item_objects)
        
        return Response({'success': 'POS Order created successfully!', 'order_id': order.id}, status=status.HTTP_201_CREATED)

class UserCancelOrderView(APIView):
    permission_classes = [IsAuthenticated]

    @transaction.atomic
    def post(self, request, order_id, *args, **kwargs):
        try:
            order = Orders.objects.get(id=order_id, user=request.user)
        except Orders.DoesNotExist:
            return Response(
                {"error": "Order not found or you do not have permission to cancel it."},
                status=status.HTTP_404_NOT_FOUND
            )

        if order.status != 'pending':
            return Response(
                {"error": f"Cannot cancel an order with status '{order.status}'."},
                status=status.HTTP_400_BAD_REQUEST
            )

        order.status = 'cancelled'
        order.save()
        
        return Response(
            {"success": f"Order {order.order_number} has been cancelled."},
            status=status.HTTP_200_OK
        )
    
class SalesReportView(generics.ListAPIView):
    serializer_class = SalesReportSerializer
    permission_classes = [IsAuthenticated, IsStaffUser]
    pagination_class = StandardResultsSetPagination 

    def get_queryset(self):
        queryset = Orders.objects.filter(status='completed').select_related(
            'user', 'processed_by_staff'
        ).prefetch_related('order_items__variation__menu_item')

        start_date_str = self.request.query_params.get('start_date', None)
        end_date_str = self.request.query_params.get('end_date', None)

        start_date = parse_date(start_date_str) if start_date_str else None
        end_date = parse_date(end_date_str) if end_date_str else None

        if start_date and end_date:
            current_tz = timezone.get_current_timezone()
            
            start_datetime = timezone.make_aware(datetime.combine(start_date, time.min), current_tz)
            
            next_day_date = end_date + timedelta(days=1)
            end_datetime_exclusive = timezone.make_aware(datetime.combine(next_day_date, time.min), current_tz)

            #DEBUGGING FOR NOW DUE TO TIME ISSUES
            print(f"Start Date from Frontend: {start_date}")
            print(f"End Date from Frontend: {end_date}")
            print(f"Django TIME_ZONE: {current_tz}")
            print(f"Query Start Datetime (Local): {start_datetime}")
            print(f"Query End Datetime (Local): {end_datetime_exclusive}")
            print("----------------------")
            
            queryset = queryset.filter(
                processed_at__gte=start_datetime, 
                processed_at__lt=end_datetime_exclusive
            )

        return queryset.order_by('-processed_at')


class SalesReportAllView(generics.ListAPIView):
    serializer_class = SalesReportSerializer
    permission_classes = [IsAuthenticated, IsStaffUser]

    def get_queryset(self):
        queryset = Orders.objects.filter(status='completed').select_related(
            'user', 'processed_by_staff'
        ).prefetch_related('order_items__variation__menu_item')

        start_date_str = self.request.query_params.get('start_date', None)
        end_date_str = self.request.query_params.get('end_date', None)

        start_date = parse_date(start_date_str) if start_date_str else None
        end_date = parse_date(end_date_str) if end_date_str else None

        if start_date and end_date:
            current_tz = timezone.get_current_timezone()
            start_datetime = timezone.make_aware(datetime.combine(start_date, time.min), current_tz)
            next_day_date = end_date + timedelta(days=1)
            end_datetime_exclusive = timezone.make_aware(datetime.combine(next_day_date, time.min), current_tz)
            
            queryset = queryset.filter(
                processed_at__gte=start_datetime, 
                processed_at__lt=end_datetime_exclusive
            )

        return queryset.order_by('-processed_at')