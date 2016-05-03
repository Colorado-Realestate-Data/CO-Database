from dateutil import parser
from rest_framework import viewsets, serializers
from rest_framework.response import Response
from rest_framework.decorators import detail_route

from .serializers import PropertySerializer, OwnerSerializer, \
    OwnerAddressSerializer, PropertyAddressSerializer, AccountSerializer, \
    LienAuctionSerializer, PropertyHistorySerializer, OwnerHistorySerializer
from prop.models import Property, Owner, OwnerAddress, PropertyAddress, \
    Account, LienAuction


class HistoricalViewMixin(object):

    MAX_HISTORY_RECORDS_NUM = 100
    history_serializer_class = None
    history_types_map = {
        'created': '+',
        'changed': '~',
        'deleted': '-',
    }

    def filter_history_by_param(self, queryset, request):
        return queryset

    def get_history_filters_by_params(self, request, queryset):
        params = request.query_params
        query_args = {}
        for k in ['history_date__gte', 'history_date__lte']:
            if k in params:
                try:
                    dt = parser.parse(params[k])
                except ValueError:
                    raise serializers.ValidationError(
                        {k: 'Invalid date format'})
                query_args[k] = dt

        if 'history_type__in' in params:
            htypes = [self.history_types_map.get(t.lower()) for t in
                      params['history_type__in'].split(',')]
            valid_htypes = {h.lower() for h in self.history_types_map.keys()}
            if not set(htypes).issubset(set(self.history_types_map.values())):
                msg = 'valid valuses are: {}'.format(valid_htypes)
                raise serializers.ValidationError({'history_type__in': msg})

            query_args['history_type__in'] = htypes

        return queryset.filter(**query_args)

    @detail_route(methods=['get'])
    def history(self, request, pk=None):
        instance = self.get_object()
        queryset = instance.history.order_by('history_type').all()
        queryset = self.get_history_filters_by_params(request, queryset)

        SerializerClass = self.history_serializer_class or \
            self.get_serializer_class()
        result = []
        for h in queryset[:self.MAX_HISTORY_RECORDS_NUM]:
            result.append({
                'object': SerializerClass(h.history_object).data,
                'history_id': h.history_id,
                'history_date': h.history_date,
                'history_type': h.get_history_type_display()
            })
        return Response(result)


class PropertyView(viewsets.ModelViewSet, HistoricalViewMixin):
    """ rest api Property resource. """

    queryset = Property.objects.all()
    serializer_class = PropertySerializer
    filter_fields = ('parid', 'county', 'timestamp')
    ordering_fields = '__all__'
    history_serializer_class = PropertyHistorySerializer


class OwnerView(viewsets.ModelViewSet, HistoricalViewMixin):
    """ rest api Owner resource. """

    queryset = Owner.objects.all()
    serializer_class = OwnerSerializer
    filter_fields = ('name', 'dba', 'ownico', 'other', 'timestamp',
                     'properties')
    ordering_fields = '__all__'
    history_serializer_class = OwnerHistorySerializer


class OwnerAddressView(viewsets.ModelViewSet, HistoricalViewMixin):
    """ rest api OwnerAddress resource. """

    queryset = OwnerAddress.objects.all()
    serializer_class = OwnerAddressSerializer
    filter_fields = ('idhash', 'street1', 'street2', 'city', 'state',
                     'zipcode', 'zip4', 'standardized', 'tiger_line_id',
                     'tiger_line_side', 'timestamp', 'owner')
    ordering_fields = '__all__'


class PropertyAddressView(viewsets.ModelViewSet, HistoricalViewMixin):
    """ rest api PropertyAddress resource. """

    queryset = PropertyAddress.objects.all()
    serializer_class = PropertyAddressSerializer
    filter_fields = ('idhash', 'street1', 'street2', 'city', 'state',
                     'zipcode', 'zip4', 'standardized', 'tiger_line_id',
                     'tiger_line_side', 'timestamp', 'property')
    ordering_fields = '__all__'


class AccountView(viewsets.ModelViewSet):
    """ rest api Account resource. """

    queryset = Account.objects.all()
    serializer_class = AccountSerializer
    filter_fields = ('property', 'tax_year', 'tax_type', 'effective_date',
                     'amount', 'balance', 'timestamp')
    ordering_fields = '__all__'


class LienAuctionView(viewsets.ModelViewSet):
    """ rest api LienAuction resource. """

    queryset = LienAuction.objects.all()
    serializer_class = LienAuctionSerializer
    filter_fields = ('property', 'face_value', 'tax_year', 'name',
                     'winning_bid', 'timestamp')
    ordering_fields = '__all__'
