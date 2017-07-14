from rest_framework.response import Response
from rest_framework.views import exception_handler
from rest_framework.permissions import DjangoModelPermissions
from django_filters.filters import EMPTY_VALUES, OrderingFilter
from rest_framework.pagination import PageNumberPagination, _positive_int


class CustomPagination(PageNumberPagination):
    ''' Custom Pagination to be used in rest api'''

    BIG_PAGE_SIZE = 10000000
    page_size_query_param = 'page_size'

    def paginate_queryset(self, queryset, request, view=None):
        if view:
            max_page_size = getattr(view, 'max_page_size', self.max_page_size)
            if max_page_size is None:
                from django.conf import settings
                max_page_size = settings.REST_FRAMEWORK.get('MAX_PAGE_SIZE_DEFAULT', 100)
            self.max_page_size = self.BIG_PAGE_SIZE if max_page_size == 0 else max_page_size
        return super(CustomPagination, self).paginate_queryset(queryset, request, view=view)

    def get_page_size(self, request):
        '''
        this is overrided to allow 0 as a page_size.
        if page_size=0, we will set page_size as max_page_size.
        '''
        page_size = self.page_size
        if self.page_size_query_param:
            try:
                page_size = _positive_int(
                    request.query_params[self.page_size_query_param],
                    strict=False,
                    cutoff=self.max_page_size
                )
            except (KeyError, ValueError):
                pass
        if page_size == 0:
            page_size = self.max_page_size
        return page_size

    def get_paginated_response(self, data):
        ''' override pagination structure in list rest api '''

        next_page = self.page.next_page_number() if \
            self.page.has_next() else None
        previous_page = self.page.previous_page_number() if \
            self.page.has_previous() else None
        return Response({
            'pagination': {
                'next_url': self.get_next_link(),
                'previous_url': self.get_previous_link(),
                'current_page': self.page.number,
                'next_page': next_page,
                'previous_page': previous_page,
                'first_page': 1,
                'last_page': self.page.paginator.num_pages,
                'page_size': self.get_page_size(self.request),
                'count': self.page.paginator.count,
            },
            'results': data
        })


def custom_rest_exception_handler(exc, context):
    ''' Custom rest api exception handler '''
    from rest_framework import exceptions
    response = exception_handler(exc, context)
    if isinstance(exc, exceptions.NotAuthenticated):
        response.status_code = 401
    if isinstance(exc, exceptions.ValidationError) and \
            ('already exists' in str(exc) or
             'must make a unique set' in str(exc)):
        response.status_code = 409

    return response


class DynamicFieldsSerializerMixin(object):
    '''
    This class allow you to have dynamic fields in get rest api.
    user can pass "fields" and "xfields" as a get query parameter.
    "fields" specify list of fields you want to be shown as a result.
    "xfields" specify list of fields you want to be excluded in result.
    i.e:
    fields=id,name
    or
    xfields=name1,name2
    '''
    def __init__(self, *args, **kwargs):
        super(DynamicFieldsSerializerMixin, self).__init__(*args, **kwargs)
        if not self.context:
            return

        params = self.context['request'].query_params
        fields = params.get('fields')
        xfields = params.get('xfields')
        if fields:
            fields = fields.split(',')
            allowed = set(fields)
            existing = set(self.fields.keys())
            for field_name in existing - allowed:
                self.fields.pop(field_name)
        elif xfields:
            xfields = xfields.split(',')
            for field_name in xfields:
                self.fields.pop(field_name, None)


class ExtendedOrderingFilter(OrderingFilter):
    def __init__(self, *args, **kwargs):
        self.ordering_map = kwargs.pop('ordering_map', {})
        super(ExtendedOrderingFilter, self).__init__(*args, **kwargs)

    def get_ordering_value(self, param):
        descending = param.startswith('-')
        param = param[1:] if descending else param
        field_name = self.param_map.get(param, param)
        field_name = self.ordering_map.get(field_name, field_name)
        if isinstance(field_name, str):
            field_name = (field_name,)

        return [("-%s" % f if descending else f) for f in field_name ]

    def filter(self, qs, value):
        if value in EMPTY_VALUES:
            return qs

        ordering = []
        for param in value:
            ordering.extend(list(self.get_ordering_value(param)))
        return qs.order_by(*ordering)


class CustomDjangoModelPermissions(DjangoModelPermissions):
    perms_map = {
        'OPTIONS': [],
        'HEAD': [],
        'GET': ['%(app_label)s.view_%(model_name)s'],
        'POST': ['%(app_label)s.add_%(model_name)s'],
        'PUT': ['%(app_label)s.change_%(model_name)s'],
        'PATCH': ['%(app_label)s.change_%(model_name)s'],
        'DELETE': ['%(app_label)s.delete_%(model_name)s'],
    }
