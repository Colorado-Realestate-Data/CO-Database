import django_filters
from prop.models import Property, Account, LienAuction
from rest_framework import filters


class PropertyFilter(filters.FilterSet):
    min_timestamp = django_filters.IsoDateTimeFilter(name="timestamp",
                                                     lookup_type="gte")
    max_timestamp = django_filters.IsoDateTimeFilter(name="timestamp",
                                                     lookup_type="lte")

    class Meta:
        model = Property
        fields = ["parid", "county", "min_timestamp", "max_timestamp"]


class AccountFilter(filters.FilterSet):
    min_tax_year = django_filters.NumberFilter(name="tax_year",
                                               lookup_type="gte")
    max_tax_year = django_filters.NumberFilter(name="tax_year",
                                               lookup_type="lte")
    min_amount = django_filters.NumberFilter(name="amount",
                                             lookup_type="gte")
    max_amount = django_filters.NumberFilter(name="amount",
                                             lookup_type="lte")
    min_balance = django_filters.NumberFilter(name="balance",
                                              lookup_type="gte")
    max_balance = django_filters.NumberFilter(name="balance",
                                              lookup_type="lte")

    class Meta:
        model = Account
        fields = ['property', 'tax_type', 'effective_date', 'timestamp',
                  'tax_year', 'min_tax_year', 'max_tax_year',
                  'amount', 'min_amount', 'max_amount',
                  'balance', 'min_balance', 'max_balance',
                  ]


class AccountTaxTypeSummaryFilter(filters.FilterSet):
    min_tax_year = django_filters.NumberFilter(name="tax_year",
                                               lookup_type="gte")
    max_tax_year = django_filters.NumberFilter(name="tax_year",
                                               lookup_type="lte")

    class Meta:
        model = Account
        fields = ['tax_year', 'min_tax_year', 'max_tax_year',
                  'property__parid', ]


class LienAuctionFilter(filters.FilterSet):
    min_tax_year = django_filters.NumberFilter(name="tax_year",
                                               lookup_type="gte")
    max_tax_year = django_filters.NumberFilter(name="tax_year",
                                               lookup_type="lte")
    min_face_value = django_filters.NumberFilter(name="face_value",
                                                 lookup_type="gte")
    max_face_value = django_filters.NumberFilter(name="face_value",
                                                 lookup_type="lte")
    min_winning_bid = django_filters.NumberFilter(name="winning_bid",
                                                  lookup_type="gte")
    max_winning_bid = django_filters.NumberFilter(name="winning_bid",
                                                  lookup_type="lte")

    class Meta:
        model = LienAuction
        fields = ['property', 'name', 'timestamp',
                  'tax_year', 'min_tax_year', 'max_tax_year',
                  'face_value', 'min_face_value', 'max_face_value',
                  'winning_bid', 'min_winning_bid', 'max_winning_bid',
                  ]
