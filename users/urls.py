# users/urls.py
from django.urls import path
from .views import RegisterView, MyTokenObtainPairView, AdminDashboardDataView, StaffUserListView, StaffUserDetailView, UserProfileView, ActivateAccountView, RequestPasswordResetView, PasswordResetConfirmView, ChangePasswordView
from rest_framework_simplejwt.views import TokenRefreshView

urlpatterns = [
    path('register/', RegisterView.as_view(), name='register'),
    path('token/', MyTokenObtainPairView.as_view(), name='token_obtain_pair'), 
    path('token/refresh/', TokenRefreshView.as_view(), name='token_refresh'),
    path('admin/dashboard-data/', AdminDashboardDataView.as_view(), name='admin_dashboard_data'),

    path('profile/', UserProfileView.as_view(), name='user-profile'),
    path('change-password/', ChangePasswordView.as_view(), name='change-password'),


    path('admin/staff/', StaffUserListView.as_view(), name='admin-staff-list'),
    path('admin/staff/<int:id>/', StaffUserDetailView.as_view(), name='admin-staff-detail'),

    path('activate/<str:uidb64>/<str:token>/', ActivateAccountView.as_view(), name='activate'), 

    path('password-reset/', RequestPasswordResetView.as_view(), name='password-reset-request'),
    path('password-reset/confirm/<str:uidb64>/<str:token>/', PasswordResetConfirmView.as_view(), name='password-reset-confirm'),
]