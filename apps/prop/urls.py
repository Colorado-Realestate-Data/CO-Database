from django.conf.urls import url
from rest_framework import routers
from django.urls import include
from django.conf import settings

from apps.prop.rest_api.views import *

COUNTY_BASE_ENDPOINT_PARAM = getattr(settings, 'COUNTY_BASE_ENDPOINT_PARAM', 'county')
VERSION_PARAM = settings.REST_FRAMEWORK.get('VERSION_PARAM', 'version')
DEFAULT_VERSION = settings.REST_FRAMEWORK.get('DEFAULT_VERSION', 'v1')


API_ENDPOINT = 'api/(?P<{}>v\d+)'.format(VERSION_PARAM)

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
general_rest_router.register(r'session', SessionView, base_name='session')
general_rest_router.register(r'me', ProfileView, base_name='profile')

app_name = 'prop'

urlpatterns = [
    url(r'^{}/', include(general_rest_router.urls)),
    url(r'^(?P<{}>[^/]+)/{}/'.format(COUNTY_BASE_ENDPOINT_PARAM, API_ENDPOINT), include(county_base_rest_router.urls)),
]
