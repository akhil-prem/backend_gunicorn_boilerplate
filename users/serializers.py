from rest_framework import serializers
from .models import Account, Invitation
from django.contrib.auth.models import User





class UserSerializer(serializers.ModelSerializer):
    # password = serializers.CharField(
    #     max_length=65, min_length=8, write_only=True)
    # email = serializers.EmailField(max_length=255, min_length=4),
    # first_name = serializers.CharField(max_length=255, min_length=2)
    # last_name = serializers.CharField(max_length=255, min_length=2)

    class Meta:
        model = Account
        # extra_kwargs = {'password': {'write_only': True}}
        fields = ["last_login",
                  "email",
                  "username",
                  "first_name",
                  "last_name",
                  "is_active",
                  "is_admin",
                  "is_staff",
                  "avatar", 
                  ]

    # def validate(self, attrs):
    #     email = attrs.get('email', '')
    #     if User.objects.filter(email=email).exists():
    #         raise serializers.ValidationError(
    #             {'email': ('Email is already in use')})
    #     return super().validate(attrs)

    # def create(self, validated_data):
    #     return User.objects.create_user(**validated_data)


class LoginSerializer(serializers.ModelSerializer):
    password = serializers.CharField(
        max_length=65, min_length=8, write_only=True)
    username = serializers.CharField(max_length=255, min_length=2)

    class Meta:
        model = User
        fields = ['email', 'password']
        
        
class AccountSerializer(serializers.ModelSerializer):
    class Meta:
        model = Account
        extra_kwargs = {'password': {'write_only': True}}
        fields = '__all__'

class InvitationSerializer(serializers.Serializer):
    email = serializers.EmailField()
    firstname = serializers.CharField()
    lastname = serializers.CharField()
    is_admin = serializers.BooleanField()

class ActivateUserSerializer(serializers.Serializer):
    email = serializers.EmailField()
    password = serializers.CharField(
        min_length=4,
        max_length=10,
        write_only=True,
        required=True,
        style={'input_type': 'password'}
        )

class ProfileSerializer(serializers.ModelSerializer):
    class Meta:
        model = Account
        fields = ['first_name', 'last_name']

class AvatarUpdateSerializer(serializers.Serializer):
    avatar = serializers.CharField()

class ChangePasswordSerializer(serializers.Serializer):
    old_password = serializers.CharField(
        min_length=4,
        max_length=20,
        write_only=True,
        required=True,
        style={'input_type': 'password'}
        )
    new_password = serializers.CharField(
        min_length=4,
        max_length=10,
        write_only=True,
        required=True,
        style={'input_type': 'password'}
        )

class ForgotPasswordSerializer(serializers.Serializer):
    retrieve_password_otp = serializers.IntegerField()
    password = serializers.CharField(
        min_length=4,
        max_length=10,
        write_only=True,
        required=True,
        style={'input_type': 'password'}
        )

class InvitationSerializer(serializers.Serializer):
    email = serializers.EmailField()
    firstname = serializers.CharField()
    lastname = serializers.CharField()
    is_admin = serializers.BooleanField()





class InvitedUsersSerializer(serializers.ModelSerializer):
    class Meta:
        model = Invitation
        fields = "__all__"
        # exclude = ('inviting_key', 'registration_key')

class ActivateUserSerializer(serializers.Serializer):
    email = serializers.EmailField()
    password = serializers.CharField(
        min_length=4,
        max_length=10,
        write_only=True,
        required=True,
        style={'input_type': 'password'}
        )
