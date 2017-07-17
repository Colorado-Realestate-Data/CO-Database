import types
from django.conf import settings
from django.http import JsonResponse
from rest_framework.generics import get_object_or_404
from rest_framework.response import Response

CURRENT_COUNTY_ATTR_NAME = getattr(settings, 'CURRENT_COUNTY_ATTR_NAME', '_current_county')
COUNTY_BASE_ENDPOINT_PARAM = getattr(settings, 'COUNTY_BASE_ENDPOINT_PARAM', 'county')

from threading import local
_thread_locals = local()


def _do_set_current_county(county_func):
    setattr(_thread_locals, CURRENT_COUNTY_ATTR_NAME, types.MethodType(county_func, _thread_locals))


def _set_current_county(county=None):
    '''
    Sets current county in local thread.

    Can be used as a hook e.g. for shell jobs (when request object is not available).
    '''
    _do_set_current_county(lambda self: county)


class CurrentCountyMiddleware(object):

    def process_view(self, request, view_func, view_args, view_kwargs):
        from prop.models import County
        if COUNTY_BASE_ENDPOINT_PARAM in view_kwargs:
            county_name = view_kwargs[COUNTY_BASE_ENDPOINT_PARAM]
            county = County.objects.filter(name=county_name).first()
            if not county:
                return JsonResponse({'error': '[{}] county does not exists!'.format(county_name)}, status=404)
            if county and not county.active:
                return JsonResponse({'error': '[{}] county is not active!'.format(county_name)}, status=404)
            setattr(request, COUNTY_BASE_ENDPOINT_PARAM, county)
        _do_set_current_county(lambda self: getattr(request, COUNTY_BASE_ENDPOINT_PARAM, None))


def get_current_county():
    current_county = getattr(_thread_locals, CURRENT_COUNTY_ATTR_NAME, None)
    return current_county() if current_county else current_county


def get_current_county_id():
    county = get_current_county()
    return county and county.id
