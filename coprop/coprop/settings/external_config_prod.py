DEBUG = False

ALLOWED_HOSTS = ['*']

DATABASES = {
    'default': {
        'ENGINE': 'django.db.backends.postgresql_psycopg2',
        'NAME': 'coprop',
        'HOST': 'cinnamonhillsdev.c704tm2jtvlo.us-west-2.rds.amazonaws.com',
        'PORT': '5432',
        'USER': 'chills',
        'PASSWORD': 'raWoDwigaKaUYW'
    }
}
