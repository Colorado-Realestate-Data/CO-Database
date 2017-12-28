import django_filters
import operator
from functools import reduce
from django.contrib.auth.models import Group, Permission
from django.db.models import Q
from rest_framework import filters

from prop.models import User


class UserFilter(filters.FilterSet):
    min_date_joined = django_filters.IsoDateTimeFilter(name="date_joined", lookup_expr="gte")
    max_date_joined = django_filters.IsoDateTimeFilter(name="date_joined", lookup_expr="lte")
    min_last_login = django_filters.IsoDateTimeFilter(name="last_login", lookup_expr="gte")
    max_last_login = django_filters.IsoDateTimeFilter(name="last_login", lookup_expr="lte")
    name = django_filters.CharFilter(label='Name', method='name_method')

    def name_method(self, queryset, name, value):
        search_fields = ['first_name', 'last_name']
        query = reduce(operator.or_, (Q(**{'{}__icontains'.format(f): value}) for f in search_fields))
        return queryset.filter(query)

    class Meta:
        model = User
        fields = ['is_superuser', 'username', 'email', 'is_staff', 'is_active']


class GroupFilter(filters.FilterSet):

    class Meta:
        model = Group
        fields = ['name']


class PermissionFilter(filters.FilterSet):
    codename = django_filters.BaseInFilter(name='codename')

    class Meta:
        model = Permission
        fields = ['name', 'codename']
