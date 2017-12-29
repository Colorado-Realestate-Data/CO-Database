import inspect
import sys
import simplejson as json
from django.conf import settings
from dateutil import parser
from django.contrib.auth import authenticate, login, logout
from rest_framework import viewsets, serializers, permissions
from rest_framework.generics import get_object_or_404
from rest_framework.parsers import FileUploadParser
from rest_framework.response import Response
from rest_framework.decorators import detail_route, list_route
from djoser.views import SetPasswordView as JoserSetPasswordView
from django.db.models import Sum
from reversion.models import Version

from .serializers import PropertySerializer, OwnerSerializer, \
    OwnerAddressSerializer, PropertyAddressSerializer, AccountSerializer, \
    LienAuctionSerializer, CountySerializer, UserProfileSerializer, UserSerializer, AvatarSerializer, SessionSerializer
from apps.prop.models import Property, Owner, OwnerAddress, PropertyAddress, \
    Account, LienAuction, County
from .filters import PropertyFilter, AccountFilter, LienAuctionFilter, \
    AccountTaxTypeSummaryFilter, PropertyTaxTypeSummaryFilter

COUNTY_BASE_ENDPOINT_PARAM = getattr(settings, 'COUNTY_BASE_ENDPOINT_PARAM', 'county')

__all__ = (
    "PropertyView",
    "OwnerView",
    "OwnerAddressView",
    "PropertyAddressView",
    "AccountView",
    "LienAuctionView",
    "CountyView",
    "SessionView",
    "ProfileView",
    "SetPasswordView",
)


class SessionView(viewsets.ViewSet):
    class SessionPermission(permissions.BasePermission):
        """ custom class to check permissions for sessions """

        def has_permission(self, request, view):
            """ check request permissions """
            if request.method == 'POST':
                return True
            return request.user.is_authenticated() and request.user.is_active

    permission_classes = (SessionPermission,)
    serializer_class = SessionSerializer

    def initialize_request(self, request, *args, **kwargs):
        request = super(SessionView, self).initialize_request(request, *args, **kwargs)
        if request.method == 'POST':
            # remove authentication_classes to dont check csrf
            request.authenticators = []
        return request

    def get(self, request, *args, **kwargs):
        """ api to get current session """

        return Response(UserSerializer(request.user).data)

    def post(self, request, *args, **kwargs):
        """ api to login """
        serializer = self.serializer_class(data=request.data)
        serializer.is_valid(raise_exception=True)
        user = authenticate(**serializer.data)
        if not user:
            return Response({'reason': 'Username or password is incorrect'},
                            status=400)
        if not user.is_active:
            return Response({'reason': 'User is inactive'}, status=403)

        login(request, user)
        return Response(UserSerializer(user).data)

    def delete(self, request, *args, **kwargs):
        """ api to logout """

        user_id = request.user.id
        logout(request)
        return Response({'id': user_id})

    create = post  # this is a trick to show this view in api-root


class ProfileView(viewsets.ViewSet):
    permission_classes = (permissions.IsAuthenticated,)
    serializer_class = UserProfileSerializer
    parser_classes = list(viewsets.ViewSet.parser_classes) + [FileUploadParser]

    def list(self, request, *args, **kwargs):
        return Response(UserSerializer(request.user).data)

    def put(self, request, *args, **kwargs):
        serializer = self.serializer_class(instance=request.user, data=request.data)
        serializer.is_valid(raise_exception=True)
        user = serializer.save()
        return Response(UserSerializer(user).data)

    def __update_avatar(self, request, *args, **kwargs):
        profile = request.user.profile
        file_obj = request.data['file']
        serializer = AvatarSerializer(instance=profile, data={'avatar': file_obj})
        serializer.is_valid(raise_exception=True)
        serializer.save()
        avatar_url = None
        if profile.avatar:
            avatar_url = profile.avatar.url
        return Response({'avatar': avatar_url})

    def __delete_avatar(self, request, *args, **kwargs):
        profile = request.user.profile
        profile.avatar = None
        profile.save()
        return Response({'avatar': None})

    @list_route(methods=['delete', 'put'])
    def avatar(self, request, *args, **kwargs):
        if self.request.method == 'DELETE':
            return self.__delete_avatar(request, **kwargs)
        elif self.request.method == 'PUT':
            return self.__update_avatar(request, **kwargs)

        raise Exception('should not reach here!')

    create = put


class SetPasswordView(JoserSetPasswordView):
    def post(self, request, *args, **kwargs):
        return super(SetPasswordView, self).post(request)


class CountyViewSetMixin(object):
    """
    a base connty modelviewset class for all other viewsets.
    Notice!!! using this class in multi-inheritance as a "first" parent class.
    i.e: class PropertyView(CountyViewSetMixin, viewsets.ModelViewSet, HistoricalViewMixin)
    """
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

#############################################################################################
### !!! dont touch this section. we need this section to patch some views to inject some data !!!
#############################################################################################
# def _perd(c):
#     return inspect.isclass(c) and c.__module__ == _perd.__module__
#
#
# classes = inspect.getmembers(sys.modules[__name__], _perd)
# for class_name, klass in classes:
#     if not issubclass(klass, CountyViewSetMixin) or not issubclass(klass, viewsets.ModelViewSet):
#         continue
#     if getattr(klass, 'ordering_fields') == '__all__':
#         qs = getattr(klass, 'queryset', None)
#         model = qs and getattr(qs, 'model', None)
#         if not model:
#             continue
#         klass.ordering_fields = [f.name for f in model._meta.fields if f.name != 'county']
