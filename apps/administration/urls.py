from rest_framework import routers
from django.urls import include, path

from apps.administration.rest_api.views import UserView, GroupView, PermissionView

admin_rest_router = routers.DefaultRouter()
admin_rest_router.trailing_slash = "/?"  # added to support both / and slashless
admin_rest_router.register(r'user', UserView)
admin_rest_router.register(r'group', GroupView)
admin_rest_router.register(r'permission', PermissionView)

app_name = 'administration'

urlpatterns = [
    path('', include(admin_rest_router.urls))
]
