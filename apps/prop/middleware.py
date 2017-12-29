import types
from django.conf import settings
from django.http import JsonResponse
from threading import local
from django.core.cache import cache

CURRENT_COUNTY_ATTR_NAME = getattr(settings, 'CURRENT_COUNTY_ATTR_NAME', '_current_county')
COUNTY_BASE_ENDPOINT_PARAM = getattr(settings, 'COUNTY_BASE_ENDPOINT_PARAM', 'county')
_thread_locals = local()


def _do_set_current_county(county_func):
    setattr(_thread_locals, CURRENT_COUNTY_ATTR_NAME, types.MethodType(county_func, _thread_locals))


def _set_current_county(county=None):
    """
    Sets current county in local thread.

    Can be used as a hook e.g. for shell jobs (when request object is not available).
    """
    _do_set_current_county(lambda self: county)


COUNTY_CACHE_KEY = cache_key = 'middleware-county-{county_name}'


def get_county_cached(county_name):
    from apps.prop.models import County
    cache_key = COUNTY_CACHE_KEY.format(county_name=county_name)
    NOT_EXISTS = object()
    county = cache.get(cache_key, NOT_EXISTS)
    if county == NOT_EXISTS:
        county = County.objects.filter(name=county_name).first()
        if county:
            county = {k: v for k, v in county.__dict__.items() if not k.startswith('_')}
        cache.set(cache_key, county)
    return county


def clear_county_cached(county_name):
    cache_key = COUNTY_CACHE_KEY.format(county_name=county_name)
    cache.delete(cache_key)


class CurrentCountyMiddleware:

    def process_view(self, request, view_func, view_args, view_kwargs):
        if COUNTY_BASE_ENDPOINT_PARAM in view_kwargs:
            county_name = view_kwargs[COUNTY_BASE_ENDPOINT_PARAM]
            county = get_county_cached(county_name)
            if not county:
                return JsonResponse({'error': '[{}] county does not exists!'.format(county_name)}, status=404)
            if county and not county.get('active'):
                return JsonResponse({'error': '[{}] county is not active!'.format(county_name)}, status=404)
            setattr(request, COUNTY_BASE_ENDPOINT_PARAM, county)
        _do_set_current_county(lambda self: getattr(request, COUNTY_BASE_ENDPOINT_PARAM, None))


def get_current_county():
    current_county = getattr(_thread_locals, CURRENT_COUNTY_ATTR_NAME, None)
    return current_county() if current_county else current_county


def get_current_county_id():
    county = get_current_county()
    return county and county.get('id')
