# For beginners: This file (config/settings/local.py) contains part of the application logic.
# For beginners: Read this file from top to bottom to see what data it handles
# and which functions/classes other files can call.

"""
Local development settings.
"""

from .base import *  # noqa

DEBUG = True
ALLOWED_HOSTS = ['localhost', '127.0.0.1', '.ngrok-free.app']


DATABASES = {
    'default': {
        'ENGINE': 'django.db.backends.postgresql',
        'NAME': 'isaac',                      
        'USER': 'isaac',
        'PASSWORD': 'Lubuntu@123',
        'DBNAME': 'isaac',
        'HOST': 'localhost',
        'PORT': '5432',
    }
}


# Email backend for local testing
EMAIL_BACKEND = 'django.core.mail.backends.console.EmailBackend'

# Disable SSL redirect for local development
SECURE_SSL_REDIRECT = False

# CORS for local frontend
CORS_ALLOWED_ORIGINS = [
    'http://localhost:3000',
    'http://localhost:5000',
    'http://localhost:8000',
    'http://127.0.0.1:3000',
]

# Q Cluster configuration for local development (use disque instead of ORM)
Q_CLUSTER = {
    'name': 'bima_afya',
    'workers': 2,
    'timeout': 500,
    'retry': 600,
    'queue_limit': 10,
    'bulk': 5,
    'orm': 'default',
    'catch_up': False,
    'debug': True,
}
