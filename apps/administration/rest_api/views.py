from django.contrib.auth.models import Group, Permission
from rest_framework import viewsets, permissions, status
from rest_framework.decorators import detail_route
from rest_framework.response import Response

from apps.prop.models import User
from project.helpers.utils import CustomDjangoModelPermissions
from .filters import UserFilter, GroupFilter, PermissionFilter
from .serializers import UserSerializer, GroupSerializer, PermissionSerializer, ChangePasswordSerializer

ADMIN_PERMISSION_CLASSES = (permissions.IsAdminUser, CustomDjangoModelPermissions)


class UserView(viewsets.ModelViewSet):
    permission_classes = ADMIN_PERMISSION_CLASSES
    max_page_size = 0
    queryset = User.objects.all()
    serializer_class = UserSerializer
    filter_class = UserFilter
    ordering = 'id'
    ordering_fields = ('id', 'last_login', 'is_superuser', 'username', 'first_name', 'last_name', 'email', 'is_staff',
                       'is_active', 'date_joined')

    @detail_route(methods=['put'], serializer_class=ChangePasswordSerializer)
    def set_password(self, request, *args, **kwargs):
        user = self.get_object()
        serializer = self.get_serializer(data=request.data)
        serializer.is_valid(raise_exception=True)
        user.set_password(serializer.data['password'])
        user.save()
        return Response(status=status.HTTP_204_NO_CONTENT)


class GroupView(viewsets.ModelViewSet):
    permission_classes = ADMIN_PERMISSION_CLASSES
    max_page_size = 0
    queryset = Group.objects.all()
    serializer_class = GroupSerializer
    filter_class = GroupFilter
    ordering = 'id'
    ordering_fields = ('id', 'name')


class PermissionView(viewsets.ReadOnlyModelViewSet):
    permission_classes = ADMIN_PERMISSION_CLASSES
    max_page_size = 0
    queryset = Permission.objects.all()
    serializer_class = PermissionSerializer
    filter_class = PermissionFilter
    ordering = 'id'
    ordering_fields = ('id', 'name', 'codename')
