"""coprop URL Configuration

The `urlpatterns` list routes URLs to views. For more information please see:
    https://docs.djangoproject.com/en/dev/topics/http/urls/
Examples:
Function views
    1. Add an import:  from my_app import views
    2. Add a URL to urlpatterns:  url(r'^$', views.home, name='home')
Class-based views
    1. Add an import:  from other_app.views import Home
    2. Add a URL to urlpatterns:  url(r'^$', Home.as_view(), name='home')
Including another URLconf
    1. Import the include() function: from django.conf.urls import url, include
    2. Add a URL to urlpatterns:  url(r'^blog/', include('blog.urls'))
"""
from django.conf import settings
from django.urls import path
from django.views.static import serve
from django.conf.urls import url, include
from django.contrib import admin
from rest_framework_jwt.views import obtain_jwt_token, refresh_jwt_token, \
    verify_jwt_token


from apps.prop.rest_api.views import SetPasswordView
from apps.prop.views import IndexView, LoginView

COUNTY_BASE_ENDPOINT_PARAM = getattr(settings, 'COUNTY_BASE_ENDPOINT_PARAM', 'county')
VERSION_PARAM = settings.REST_FRAMEWORK.get('VERSION_PARAM', 'version')
DEFAULT_VERSION = settings.REST_FRAMEWORK.get('DEFAULT_VERSION', 'v1')


API_ENDPOINT = 'api/(?P<{}>v\d+)'.format(VERSION_PARAM)

urlpatterns = [
    path('', include('apps.prop.urls')),
    url(r'^{}/me/password'.format(API_ENDPOINT), SetPasswordView.as_view()),
    url(r'^{}/admin/'.format(API_ENDPOINT), include('apps.administration.urls')),
    url(r'^admin/', admin.site.urls),
    url(r'^api-auth/', include('rest_framework.urls', namespace='rest_framework')),
    url(r'^token/auth/', obtain_jwt_token),
    url(r'^token/refresh/', refresh_jwt_token),
    url(r'^token/verify/', verify_jwt_token),
    url(r'^$', IndexView.as_view(), name='index'),
    url(r'^login/$', LoginView.as_view(), name="login"),
]

if settings.DEBUG:
    urlpatterns += [
        url(r'^media/(.*)$', serve, {'document_root': settings.MEDIA_ROOT}),
    ]
