# menu/urls.py
from django.urls import path
from .views import (
    MenuItemListView, 
    CategoryListView,   
    AdminMenuItemListView, 
    AdminMenuItemDetailView,
    AdminVariationDetailView, 
    AdminCategoryListView, 
    AdminCategoryDetailView
)

urlpatterns = [
    path('items/', MenuItemListView.as_view(), name='menuitem-list'),
    path('categories/', CategoryListView.as_view(), name='category-list'),

    path('admin/items/', AdminMenuItemListView.as_view(), name='admin-menuitem-list-create'),
    path('admin/items/<int:id>/', AdminMenuItemDetailView.as_view(), name='admin-menuitem-detail'),
    
    path('admin/variations/<int:id>/', AdminVariationDetailView.as_view(), name='admin-variation-delete'),

    path('admin/categories/', AdminCategoryListView.as_view(), name='admin-category-list-create'),
    path('admin/categories/<int:id>/', AdminCategoryDetailView.as_view(), name='admin-category-detail'),
]