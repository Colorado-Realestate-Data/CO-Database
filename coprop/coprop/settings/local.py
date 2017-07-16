from .base import *

DEBUG = True

DATABASES = {
    'default': {
        'ENGINE': 'django.db.backends.postgresql_psycopg2',
        'NAME': 'coprop',
        'HOST': 'localhost',
        'PORT': '5432',
        'USER': 'postgres',
        'PASSWORD': 'a',
    }
}
