"""
Production settings for Azure deployment.
"""

from .base import *  # noqa
import dj_database_url

DEBUG = False
ALLOWED_HOSTS = [
    config('ALLOWED_HOSTS', default='localhost,127.0.0.1', cast=Csv())
]

# Security
SECURE_SSL_REDIRECT = True
SECURE_HSTS_SECONDS = 31536000
SECURE_HSTS_INCLUDE_SUBDOMAINS = True
SECURE_HSTS_PRELOAD = True
SESSION_COOKIE_SECURE = True
CSRF_COOKIE_SECURE = True
SECURE_CONTENT_SECURITY_POLICY = {
    'default-src': ("'self'",),
}

# Database
DATABASES = {
  'default': {
    'ENGINE': 'django.db.backends.postgresql',
      'NAME': config('DB_NAME', default='postgres'),
      'USER': config('DB_USER', default='postgres'),
      'PASSWORD': config('DB_PASSWORD', default=''),
      'HOST': config('DB_HOST', default='localhost'),
    'PORT': config('DB_PORT', default='5432'),
    'CONN_MAX_AGE': 600,
    'OPTIONS': {'sslmode': 'require'},
  }
}
# Static files with Azure
STATIC_URL = 'https://{}.blob.core.windows.net/static/'.format(AZURE_ACCOUNT_NAME)
STORAGES['staticfiles'] = {
  'BACKEND': 'storages.backends.azure_storage.AzureStorage',
  'OPTIONS': {
    'account_name': AZURE_ACCOUNT_NAME,
    'account_key': AZURE_ACCOUNT_KEY,
    'azure_container_name': AZURE_CONTAINER,
  },
}

# Email via SendGrid or similar
EMAIL_BACKEND = config(
    'EMAIL_BACKEND',
    default='django.core.mail.backends.smtp.EmailBackend'
)

# Restrict CORS to production domain only
CORS_ALLOWED_ORIGINS = [
    config('PRODUCTION_URL', default='https://bima-afya.com'),
]

# Q Cluster
Q_CLUSTER['debug'] = False
Q_CLUSTER['workers'] = 8
