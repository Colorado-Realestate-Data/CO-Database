# noinspection PyPep8Naming
import json as JSON
import re
from datetime import timedelta

import isodate
from django import template
from django.apps import apps
# noinspection PyCompatibility
from django.conf import settings
from django.urls import reverse
from django.utils.safestring import mark_safe

from coprop.helpers.utils import get_aware_datetime

register = template.Library()


@register.filter(name='addcss')
def addcss(field, css):
    return field.as_widget(attrs={"class": css})


@register.filter
def join_and(value):
    """Given a list of strings, format them with commas and spaces, but
    with 'and' at the end.

    >>> join_and(['apples', 'oranges', 'pears'])
    "apples, oranges, and pears"

    """
    # convert numbers to strings
    value = [str(item) for item in value]
    if len(value) == 0:
        return ''
    if len(value) == 1:
        return value[0]

    # join all but the last element
    all_but_last = ", ".join(value[:-1])
    return "%s, and %s" % (all_but_last, value[-1])


@register.filter
def join_by_attr(the_list, attr_name='name'):
    return ', '.join(
        str(getattr(i, attr_name)) for i in (the_list or []))


@register.filter
def ex_join(the_list, splitter=', '):
    return splitter.join(str(l) for l in (the_list or []))


# noinspection PyPep8Naming
@register.filter
def index(List, i):
    if i is None:
        return None
    return List[int(i)]


@register.filter(name='getattribute')
def getattribute(value, arg):
    """
    Gets an attribute of an object dynamically AND recursively
    from a string name
    """
    numeric_test = re.compile("^\d+$")
    if "." in str(arg):
        firstarg = str(arg).split(".")[0]
        value = getattribute(value, firstarg)
        arg = ".".join(str(arg).split(".")[1:])
        return getattribute(value, arg)
    if hasattr(value, str(arg)):
        return getattr(value, arg)
    elif hasattr(value, 'has_key') and arg in value:
        return value[arg]
    elif numeric_test.match(str(arg)) and len(value) > int(arg):
        return value[int(arg)]
    else:
        return ''


@register.filter
def json(a):
    json_str = JSON.dumps(a)
    escapes = ['<', '>', '&']
    for c in escapes:
        json_str = json_str.replace(c, r'\u%04x' % ord(c))

    return mark_safe(json_str)


json.is_safe = True


# noinspection PyPep8Naming
def _get_field(Model, field_name):
    if isinstance(Model, str):
        Model = apps.get_model(Model)

    # noinspection PyProtectedMember
    return Model._meta.get_field(field_name)


@register.simple_tag
def get_verbose_field_name(Model, field_name):
    """
    Returns verbose_name for a field.
    """
    field = _get_field(Model, field_name)
    return field.verbose_name


@register.filter
def iso_dt(s):
    if not s:
        return None
    return get_aware_datetime(s)


def _seconds_humanize(s):
    if isinstance(s, timedelta):
        s = int(s.total_seconds())
    value = ''
    if s >= 86400:
        d = s // 86400
        s = s % 86400
        value = '{} day{}'.format(d, 's' if d > 1 else '')
    if s >= 3600:
        h = s // 3600
        s = s % 3600
        value = '{}{} hour{}'.format(value + ', ' if value else '', h, 's' if h > 1 else '')
    if s >= 60:
        m = s // 60
        s = s % 60
        value = '{}{} minute{}'.format(value + ', ' if value else '', m, 's' if m > 1 else '')
    if s > 0:
        value = '{}{} second{}'.format(value + ', ' if value else '', s, 's' if s > 1 else '')
    return value


# noinspection PyAugmentAssignment
@register.filter(name='seconds_humanize')
def seconds_humanize(s):
    return _seconds_humanize(s)


# noinspection PyAugmentAssignment
@register.filter()
def seconds_to_time(s):
    return str(timedelta(seconds=s))


@register.filter()
def iso8601_humanize(s):
    return _seconds_humanize(isodate.parse_duration(s))


@register.filter
def get_item(dictionary, key):
    return dictionary.get(key)


@register.filter
def split(s, splitter=" "):
    return s.split(splitter)


@register.simple_tag()
def add_date(date, **kwargs):
    args = {}
    for a in ['seconds', 'minutes', 'hours', 'days']:
        v = kwargs.get(a)
        if v:
            args[a] = v
    if args:
        date = date + timedelta(**args)
    return date


# noinspection PyShadowingBuiltins
@register.filter
def equals(input, value):
    return input == value


@register.filter_function
def order_by(queryset, args):
    args = [x.strip() for x in args.split(',')]
    return queryset.order_by(*args)


# noinspection PyBroadException
@register.filter
def div(value, arg):
    """
    Divides the value; argument is the divisor.
    Returns empty string on any error.
    """
    try:
        value = int(value)
        arg = int(arg)
        if arg:
            return value / arg
    except:
        pass
    return ''


@register.simple_tag(takes_context=True)
def ex_url(context, name, *args, **kwargs):
    ''' External url tag '''
    hostname = context.get('hostname') or kwargs.pop('_hostname', None)
    if not hostname:
        request = context.get('request')
        hostname = request and request.get_host()
    if not hostname:
        hostname = settings.HOSTNAME

    if not name:
        return hostname
    url = reverse(name, args=args, kwargs=kwargs)
    return '{0}{1}'.format(hostname, url)


@register.filter(is_safe=False)
def subtract(value, arg):
    """subtract the arg from the value."""
    try:
        return int(value) - int(arg)
    except (ValueError, TypeError):
        try:
            return value - arg
        except Exception:
            return ''


@register.simple_tag()
def to_percent(value, total):
    return '{:.1f}'.format(100 * float(value)/total)

