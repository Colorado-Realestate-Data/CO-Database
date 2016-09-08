import simplejson as json
from dateutil import parser
from rest_framework import viewsets, serializers
from rest_framework.response import Response
from rest_framework.decorators import detail_route, list_route
from django.db.models import Sum
from reversion import revisions

from .serializers import PropertySerializer, OwnerSerializer, \
    OwnerAddressSerializer, PropertyAddressSerializer, AccountSerializer, \
    LienAuctionSerializer
from prop.models import Property, Owner, OwnerAddress, PropertyAddress, \
    Account, LienAuction
from .filters import PropertyFilter, AccountFilter, LienAuctionFilter, \
    AccountTaxTypeSummaryFilter


class HistoricalViewMixin(object):

    MAX_HISTORY_RECORDS_NUM = 100

    def get_history_filters_by_params(self, request, queryset):
        params = request.query_params
        query_args = {}
        for k, op in [('date__gte', 'gte'), ('date__lte', 'lte')]:
            if k in params:
                try:
                    dt = parser.parse(params[k])
                except ValueError:
                    raise serializers.ValidationError(
                        {k: 'Invalid date format'})
                query_args['revision__date_created__' + op] = dt

        return queryset.filter(**query_args)

    @detail_route(methods=['get'])
    def history(self, request, pk=None):
        revisions.get_for_object
        instance = self.get_object()
        queryset = revisions.get_for_object(instance)
        queryset = self.get_history_filters_by_params(request, queryset)

        result = []
        for h in queryset[:self.MAX_HISTORY_RECORDS_NUM]:
            json_data = h.serialized_data
            obj = json.loads(json_data)[0]["fields"]
            result.append({
                # 'object': SerializerClass(h.object_version.object).data,
                'object': obj,
                'id': h.pk,
                'date': h.revision.date_created
            })
        return Response(result)


class PropertyView(viewsets.ModelViewSet, HistoricalViewMixin):
    """ rest api Property resource. """

    queryset = Property.objects.all()
    serializer_class = PropertySerializer
    ordering_fields = '__all__'
    filter_class = PropertyFilter


class OwnerView(viewsets.ModelViewSet, HistoricalViewMixin):
    """ rest api Owner resource. """

    queryset = Owner.objects.all()
    serializer_class = OwnerSerializer
    filter_fields = ('name', 'dba', 'ownico', 'other', 'timestamp',
                     'properties')
    ordering_fields = '__all__'


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
    ordering_fields = '__all__'
    filter_class = AccountFilter

    @list_route()
    def tax_type_summary(self, request, **kwargs):
        qs = self.get_queryset().values('tax_type'
                                        ).annotate(amounts=Sum('amount'))
        filters = AccountTaxTypeSummaryFilter(request.query_params,
                                              queryset=qs)
        results = [r for r in filters]
        return Response(results)


class LienAuctionView(viewsets.ModelViewSet):
    """ rest api LienAuction resource. """

    queryset = LienAuction.objects.all()
    serializer_class = LienAuctionSerializer
    ordering_fields = '__all__'
    filter_class = LienAuctionFilter
