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
from django.conf.urls import url, include
from django.contrib import admin
from django.views.generic import RedirectView
from rest_framework import routers
from rest_framework.reverse import reverse_lazy
from rest_framework_jwt.views import obtain_jwt_token, refresh_jwt_token, \
    verify_jwt_token

from prop.rest_api.views import PropertyView, OwnerView, OwnerAddressView, \
    PropertyAddressView, AccountView, LienAuctionView, CountyView

county_base_rest_router = routers.DefaultRouter()
county_base_rest_router.trailing_slash = "/?"  # added to support both / and slashless
county_base_rest_router.register(r'property', PropertyView)
county_base_rest_router.register(r'owner', OwnerView)
county_base_rest_router.register(r'owner_address', OwnerAddressView)
county_base_rest_router.register(r'property_address', PropertyAddressView)
county_base_rest_router.register(r'account', AccountView)
county_base_rest_router.register(r'lien_auction', LienAuctionView)


general_rest_router = routers.DefaultRouter()
general_rest_router.trailing_slash = "/?"  # added to support both / and slashless
general_rest_router.register(r'county', CountyView)

COUNTY_BASE_ENDPOINT_PARAM = getattr(settings, 'COUNTY_BASE_ENDPOINT_PARAM', 'county')
VERSION_PARAM = settings.REST_FRAMEWORK.get('VERSION_PARAM', 'version')
DEFAULT_VERSION = settings.REST_FRAMEWORK.get('DEFAULT_VERSION', 'v1')


API_ENDPOINT = 'api/(?P<{}>v\d+)'.format(VERSION_PARAM)

urlpatterns = [
    url(r'^$',
        RedirectView.as_view(url=reverse_lazy('general_rest_api:api-root', kwargs={VERSION_PARAM: DEFAULT_VERSION}))),
    url(r'^{}/'.format(API_ENDPOINT), include(general_rest_router.urls, namespace='general_rest_api')),
    url(r'^(?P<{}>[^/]+)/{}/'.format(COUNTY_BASE_ENDPOINT_PARAM, API_ENDPOINT),
        include(county_base_rest_router.urls, namespace='county_base_rest_api')),
    url(r'^admin/', admin.site.urls),
    url(r'^api-auth/', include('rest_framework.urls', namespace='rest_framework')),
    url(r'^token/auth/', obtain_jwt_token),
    url(r'^token/refresh/', refresh_jwt_token),
    url(r'^token/verify/', verify_jwt_token),
]
