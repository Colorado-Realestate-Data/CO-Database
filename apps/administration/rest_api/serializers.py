from django.contrib.auth.models import Group, Permission
from rest_framework import serializers

from apps.prop.models import UserProfile, User
from project.helpers.utils import DynamicFieldsSerializerMixin


class NestedProfileSerializer(serializers.ModelSerializer):
    class Meta:
        model = UserProfile
        fields = ('birth_date', 'gender', 'avatar')
        read_only_fields = ('avatar', )


class NestedGroupSerializer(serializers.ModelSerializer):
    class Meta:
        model = Group
        fields = ('id', 'name')


class NestedUserSerializer(serializers.ModelSerializer):
    class Meta:
        model = User
        fields = ('id', 'username', 'first_name', 'last_name')


class PermissionSerializer(DynamicFieldsSerializerMixin, serializers.ModelSerializer):
    class Meta:
        model = Permission
        fields = ('id', 'name', 'codename')


class UserSerializer(DynamicFieldsSerializerMixin, serializers.ModelSerializer):
    profile = NestedProfileSerializer(read_only=True)
    _groups = NestedGroupSerializer(read_only=True, source='groups', many=True)
    _user_permissions = PermissionSerializer(read_only=True, source='user_permissions', many=True)

    class Meta:
        model = User
        fields = ('id', 'last_login', 'is_superuser', 'username', 'first_name', 'last_name', 'email', 'is_staff',
                  'is_active', 'date_joined', 'groups', 'user_permissions', 'profile', '_groups', '_user_permissions')


class ChangePasswordSerializer(serializers.Serializer):
    password = serializers.CharField(style={'input_type': 'password'})


class GroupSerializer(DynamicFieldsSerializerMixin, serializers.ModelSerializer):
    _permissions = PermissionSerializer(read_only=True, source='permissions', many=True)

    class Meta:
        model = Group
        fields = ('id', 'name', 'permissions', '_permissions')
