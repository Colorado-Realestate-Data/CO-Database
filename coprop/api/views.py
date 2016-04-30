from rest_framework import viewsets

from api.serializers import PropertySerializer, OwnerSerializer, \
    OwnerAddressSerializer, PropertyAddressSerializer
from api.models import Property, Owner, OwnerAddress, PropertyAddress


class PropertyView(viewsets.ModelViewSet):
    """ rest api Property resource. """

    queryset = Property.objects.all()
    serializer_class = PropertySerializer
    filter_fields = ('parid', 'county', 'timestamp')
    ordering_fields = '__all__'


class OwnerView(viewsets.ModelViewSet):
    """ rest api Owner resource. """

    queryset = Owner.objects.all()
    serializer_class = OwnerSerializer
    filter_fields = ('name', 'dba', 'ownico', 'other', 'timestamp',
                     'properties')
    ordering_fields = '__all__'


class OwnerAddressView(viewsets.ModelViewSet):
    """ rest api OwnerAddress resource. """

    queryset = OwnerAddress.objects.all()
    serializer_class = OwnerAddressSerializer
    filter_fields = ('idhash', 'street1', 'street2', 'city', 'state',
                     'zipcode', 'zip4', 'standardized', 'tiger_line_id',
                     'tiger_line_side', 'timestamp', 'owner')
    ordering_fields = '__all__'


class PropertyAddressView(viewsets.ModelViewSet):
    """ rest api PropertyAddress resource. """

    queryset = PropertyAddress.objects.all()
    serializer_class = PropertyAddressSerializer
    filter_fields = ('idhash', 'street1', 'street2', 'city', 'state',
                     'zipcode', 'zip4', 'standardized', 'tiger_line_id',
                     'tiger_line_side', 'timestamp', 'property')
    ordering_fields = '__all__'
