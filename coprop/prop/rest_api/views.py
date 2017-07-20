import inspect
import sys
import simplejson as json
from django.conf import settings
from dateutil import parser
from rest_framework import viewsets, serializers
from rest_framework.generics import get_object_or_404
from rest_framework.response import Response
from rest_framework.decorators import detail_route, list_route
from django.db.models import Sum
from reversion.models import Version

from .serializers import PropertySerializer, OwnerSerializer, \
    OwnerAddressSerializer, PropertyAddressSerializer, AccountSerializer, \
    LienAuctionSerializer, CountySerializer
from prop.models import Property, Owner, OwnerAddress, PropertyAddress, \
    Account, LienAuction, County
from .filters import PropertyFilter, AccountFilter, LienAuctionFilter, \
    AccountTaxTypeSummaryFilter, PropertyTaxTypeSummaryFilter


COUNTY_BASE_ENDPOINT_PARAM = getattr(settings, 'COUNTY_BASE_ENDPOINT_PARAM', 'county')

class CountyViewSetMixin(object):
    '''
    a base connty modelviewset class for all other viewsets.
    Notice!!! using this class in multi-inheritance as a "first" parent class.
    i.e: class PropertyView(CountyViewSetMixin, viewsets.ModelViewSet, HistoricalViewMixin)
    '''
    county_object = None
    county_url_kwarg = 'county'

    def county_filter(self, qs):
        county = getattr(self.request, COUNTY_BASE_ENDPOINT_PARAM, None)
        county_id = county and county.get('id')
        return qs.filter(county=county_id)

    def get_queryset(self):
        return self.county_filter(super(CountyViewSetMixin, self).get_queryset())


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
                    raise serializers.ValidationError({k: 'Invalid date format'})
                query_args['revision__date_created__' + op] = dt

        return queryset.filter(**query_args)

    @detail_route(methods=['get'])
    def history(self, request, *args, **kwargs):
        instance = self.get_object()
        queryset = Version.objects.get_for_object(instance)
        queryset = self.get_history_filters_by_params(request, queryset)

        result = []
        for h in queryset[:self.MAX_HISTORY_RECORDS_NUM]:
            json_data = h.serialized_data
            obj = json.loads(json_data)[0]["fields"]
            result.append({
                'object': obj,
                'id': h.pk,
                'date': h.revision.date_created
            })
        return Response(result)


class CountyView(viewsets.ReadOnlyModelViewSet):
    """ rest api Owner resource. """

    queryset = County.objects.all()
    serializer_class = CountySerializer
    pagination_class = None
    filter_fields = ('name', 'active')
    ordering = 'name'
    ordering_fields = '__all__'

    def get_serializer_context(self):
        context = super(CountyView, self).get_serializer_context() or {}
        context.update({'request': self.request})
        return context

class PropertyView(CountyViewSetMixin, viewsets.ModelViewSet, HistoricalViewMixin):
    """ rest api Property resource. """

    queryset = Property.objects.all()
    serializer_class = PropertySerializer
    ordering_fields = '__all__'
    ordering = 'id'
    filter_class = PropertyFilter

    @list_route(filter_class=PropertyTaxTypeSummaryFilter, queryset=Account.objects,
                url_path='(?P<pk>[0-9]+)/tax_type_summary', ordering_fields=['tax_year', 'amounts', 'tax_type'])
    def tax_type_summary(self, request, *args, **kwargs):
        prop_queryset = self.county_filter(Property.objects.all())
        prop = get_object_or_404(prop_queryset, pk=self.kwargs['pk'])
        self.check_object_permissions(self.request, prop)

        qs = prop.account_set.values('tax_type', 'tax_year').annotate(amounts=Sum('amount'))
        filtered_qs = self.filter_queryset(qs)
        results = [r for r in filtered_qs]
        return Response(results)


class OwnerView(CountyViewSetMixin, viewsets.ModelViewSet, HistoricalViewMixin):
    """ rest api Owner resource. """

    queryset = Owner.objects.all()
    serializer_class = OwnerSerializer
    filter_fields = ('name', 'dba', 'ownico', 'other', 'timestamp', 'properties')
    ordering = 'id'
    ordering_fields = '__all__'


class OwnerAddressView(CountyViewSetMixin, viewsets.ModelViewSet, HistoricalViewMixin):
    """ rest api OwnerAddress resource. """

    queryset = OwnerAddress.objects.all()
    serializer_class = OwnerAddressSerializer
    filter_fields = ('idhash', 'street1', 'street2', 'city', 'state', 'zipcode', 'zip4', 'standardized',
                     'tiger_line_id', 'tiger_line_side', 'timestamp', 'owner')
    ordering_fields = '__all__'
    ordering = 'id'


class PropertyAddressView(CountyViewSetMixin, viewsets.ModelViewSet, HistoricalViewMixin):
    """ rest api PropertyAddress resource. """

    queryset = PropertyAddress.objects.all()
    serializer_class = PropertyAddressSerializer
    filter_fields = ('idhash', 'street1', 'street2', 'city', 'state', 'zipcode', 'zip4', 'standardized',
                     'tiger_line_id', 'tiger_line_side', 'timestamp', 'property')
    ordering_fields = '__all__'
    ordering = 'id'


class AccountView(CountyViewSetMixin, viewsets.ModelViewSet):
    """ rest api Account resource. """

    queryset = Account.objects.all()
    serializer_class = AccountSerializer
    ordering_fields = '__all__'
    filter_class = AccountFilter
    ordering = 'id'

    @list_route(filter_class=AccountTaxTypeSummaryFilter, ordering_fields=['amounts', 'tax_type'])
    def tax_type_summary(self, request, *args, **kwargs):
        qs = self.get_queryset().values('tax_type').annotate(amounts=Sum('amount'))
        filtered_qs = self.filter_queryset(qs)
        results = [r for r in filtered_qs]
        return Response(results)


class LienAuctionView(CountyViewSetMixin, viewsets.ModelViewSet):
    """ rest api LienAuction resource. """

    queryset = LienAuction.objects.all()
    serializer_class = LienAuctionSerializer
    ordering_fields = '__all__'
    filter_class = LienAuctionFilter
    ordering = 'id'


# #############################################################################################
# !!! dont touch this section. we need this section to patch some views to inject some data !!!
# #############################################################################################
def _perd(c):
    return inspect.isclass(c) and c.__module__ == _perd.__module__

classes = inspect.getmembers(sys.modules[__name__], _perd)
for class_name, klass in classes:
    if not issubclass(klass, CountyViewSetMixin) or not issubclass(klass, viewsets.ModelViewSet):
        continue
    if getattr(klass, 'ordering_fields') == '__all__':
        qs = getattr(klass, 'queryset', None)
        model = qs and getattr(qs, 'model', None)
        if not model:
            continue
        klass.ordering_fields = [f.name for f in model._meta.fields if f.name != 'county']
