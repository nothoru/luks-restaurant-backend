# orders/urls.py
from django.urls import path
from .views import OrderCreateView, UserOrderListView, AdminOrderListView, AdminOrderDetailView, POSOrderCreateView, UserCancelOrderView, SalesReportView, SalesReportAllView

urlpatterns = [
    path('create/', OrderCreateView.as_view(), name='order-create'),
    path('my-orders/', UserOrderListView.as_view(), name='user-order-list'), 

    path('<int:order_id>/cancel/', UserCancelOrderView.as_view(), name='user-order-cancel'),

    path('admin/all/', AdminOrderListView.as_view(), name='admin-order-list'),
    path('admin/<int:id>/update/', AdminOrderDetailView.as_view(), name='admin-order-update'),
    path('admin/create-pos/', POSOrderCreateView.as_view(), name='pos-order-create'), 
    path('admin/sales-report/', SalesReportView.as_view(), name='sales-report'),
    path('admin/sales-report/all/', SalesReportAllView.as_view(), name='sales-report-all'),


]