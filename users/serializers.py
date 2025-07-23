# backend/users/serializers.py

from rest_framework import serializers
from rest_framework_simplejwt.serializers import TokenObtainPairSerializer
from django.contrib.auth.tokens import default_token_generator
from django.utils.http import urlsafe_base64_encode
from django.utils.encoding import force_bytes
from django.conf import settings
from django.utils import timezone
from rest_framework_simplejwt.exceptions import AuthenticationFailed




from .models import User
from .utils import send_email 

class MyTokenObtainPairSerializer(TokenObtainPairSerializer):
    @classmethod
    def get_token(cls, user):   
        token = super().get_token(user)
        token['first_name'] = user.first_name
        token['role'] = user.role
        return token

    def validate(self, attrs):
        email = attrs.get('email')
        password = attrs.get('password')

        user = User.objects.filter(email__iexact=email).first()

        if user is None:
            raise AuthenticationFailed('No active account found with the given credentials.', code='authentication_failed')

        if not user.is_active:
            raise AuthenticationFailed(
                'Your account is not active. Please check your email for the activation link.', 
                code='account_not_active'
            )

        data = super().validate(attrs)

        data['role'] = self.user.role
        data['id'] = self.user.id
        return data


class RegisterSerializer(serializers.ModelSerializer):
    password = serializers.CharField(
        write_only=True, required=True, min_length=8, style={'input_type': 'password'}
    )

    class Meta:
        model = User
        fields = ('email', 'password', 'first_name', 'last_name')

    def create(self, validated_data):
        user = User.objects.create_user(
            username=validated_data['email'],
            email=validated_data['email'],
            password=validated_data['password'],
            first_name=validated_data.get('first_name', ''),
            last_name=validated_data.get('last_name', ''),
            is_active=False 
        )

        user.agreed_to_terms_at = timezone.now()
        user.save(update_fields=['agreed_to_terms_at'])

        token = default_token_generator.make_token(user)
        uid = urlsafe_base64_encode(force_bytes(user.pk))

        frontend_url = "http://localhost:5173" 
        activation_link = f"{frontend_url}/activate/{uid}/{token}/"

        context = {
            'user': user,
            'activation_link': activation_link,
        }

        print("\n\n" + "="*20)
        print("!!! ATTEMPTING TO SEND ACTIVATION EMAIL !!!")
        print(f"To: {user.email}")
        print("="*20 + "\n\n")

        send_email(
            subject="Activate Your Luk's by GoodChoice Account",
            template="account_activation_email.html",
            to_email=user.email,
            context=context
        )

        return user


class StaffUserSerializer(serializers.ModelSerializer):
    password = serializers.CharField(write_only=True, required=True, min_length=8) 

    class Meta:
        model = User
        fields = ('id', 'email', 'first_name', 'last_name', 'password', 'role')
        read_only_fields = ('id', 'role')

    def create(self, validated_data):
        user = User.objects.create_user(
            username=validated_data['email'],
            email=validated_data['email'],
            password=validated_data['password'], 
            first_name=validated_data.get('first_name', ''),
            last_name=validated_data.get('last_name', ''),
            role='staff',
            is_active=False 
        )

        token = default_token_generator.make_token(user)
        uid = urlsafe_base64_encode(force_bytes(user.pk))

        frontend_url = "http://localhost:5173"
        activation_link = f"{frontend_url}/activate/{uid}/{token}/" 

        context = {
            'user': user,
            'activation_link': activation_link, 
        }

        send_email(
            subject="Welcome! Activate Your Luk's by GoodChoice Account",
            template="account_activation_email.html", 
            to_email=user.email,
            context=context
        )
        return user


class PasswordResetRequestSerializer(serializers.Serializer):
    email = serializers.EmailField(required=True)

    def validate_email(self, value):
        return value

class PasswordResetConfirmSerializer(serializers.Serializer):
    password = serializers.CharField(write_only=True, required=True, min_length=8)
    confirm_password = serializers.CharField(write_only=True, required=True)

    def validate(self, data):
        if data['password'] != data['confirm_password']:
            raise serializers.ValidationError("Passwords do not match.")
        return data


class ChangePasswordSerializer(serializers.Serializer):
    old_password = serializers.CharField(required=True)
    new_password = serializers.CharField(required=True, min_length=8)
    confirm_new_password = serializers.CharField(required=True, min_length=8)

    def validate(self, data):
        if data['new_password'] != data['confirm_new_password']:
            raise serializers.ValidationError({"new_password": "New passwords must match."})
        return data

class UserProfileSerializer(serializers.ModelSerializer):
    class Meta:
        model = User
        fields = ['id', 'email', 'first_name', 'last_name', 'role']