import django_filters
from django_filters.rest_framework import FilterSet

from apps.prop.models import Property, Account, LienAuction


class PropertyFilter(FilterSet):
    min_timestamp = django_filters.IsoDateTimeFilter(name="timestamp", lookup_expr="gte")
    max_timestamp = django_filters.IsoDateTimeFilter(name="timestamp", lookup_expr="lte")

    class Meta:
        model = Property
        fields = ["parid", "min_timestamp", "max_timestamp"]


class AccountFilter(FilterSet):
    min_tax_year = django_filters.NumberFilter(name="tax_year", lookup_expr="gte")
    max_tax_year = django_filters.NumberFilter(name="tax_year", lookup_expr="lte")
    min_amount = django_filters.NumberFilter(name="amount", lookup_expr="gte")
    max_amount = django_filters.NumberFilter(name="amount", lookup_expr="lte")
    min_balance = django_filters.NumberFilter(name="balance", lookup_expr="gte")
    max_balance = django_filters.NumberFilter(name="balance", lookup_expr="lte")

    class Meta:
        model = Account
        fields = ['property', 'tax_type', 'effective_date', 'timestamp', 'tax_year', 'min_tax_year', 'max_tax_year',
                  'amount', 'min_amount', 'max_amount', 'balance', 'min_balance', 'max_balance',]


class AccountTaxTypeSummaryFilter(FilterSet):
    min_tax_year = django_filters.NumberFilter(name="tax_year",
                                               lookup_expr="gte")
    max_tax_year = django_filters.NumberFilter(name="tax_year",
                                               lookup_expr="lte")

    class Meta:
        model = Account
        fields = ['tax_year', 'min_tax_year', 'max_tax_year', 'property', ]


class PropertyTaxTypeSummaryFilter(FilterSet):
    min_tax_year = django_filters.NumberFilter(name="tax_year",
                                               lookup_expr="gte")
    max_tax_year = django_filters.NumberFilter(name="tax_year",
                                               lookup_expr="lte")

    class Meta:
        model = Account
        fields = ['tax_year', 'min_tax_year', 'max_tax_year', 'tax_type']


class LienAuctionFilter(FilterSet):
    min_tax_year = django_filters.NumberFilter(name="tax_year", lookup_expr="gte")
    max_tax_year = django_filters.NumberFilter(name="tax_year", lookup_expr="lte")
    min_face_value = django_filters.NumberFilter(name="face_value", lookup_expr="gte")
    max_face_value = django_filters.NumberFilter(name="face_value", lookup_expr="lte")
    min_winning_bid = django_filters.NumberFilter(name="winning_bid", lookup_expr="gte")
    max_winning_bid = django_filters.NumberFilter(name="winning_bid", lookup_expr="lte")

    class Meta:
        model = LienAuction
        fields = ['property', 'name', 'timestamp', 'tax_year', 'min_tax_year', 'max_tax_year', 'face_value',
                  'min_face_value', 'max_face_value', 'winning_bid', 'min_winning_bid', 'max_winning_bid',]
