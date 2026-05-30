"""
Local development settings.
"""

from .base import *  # noqa

DEBUG = True
ALLOWED_HOSTS = ['localhost', '127.0.0.1']

# Use SQLite for local development
DATABASES = {
    'default': {
        'ENGINE': 'django.db.backends.sqlite3',
        'NAME': BASE_DIR / 'db.sqlite3',
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
    'orm': 'default',  # Use Django ORM with SQLite
    'catch_up': False,
    'debug': True,
}
