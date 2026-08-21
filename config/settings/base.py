# For beginners: This file (config/settings/base.py) contains part of the application logic.
# For beginners: Read this file from top to bottom to see what data it handles
# and which functions/classes other files can call.

"""
Django settings for Bima Afya project.
Base settings shared between local and production environments.
"""

import os
from datetime import timedelta
from pathlib import Path
from decouple import Config, RepositoryEnv, Csv
import dj_database_url

# Build paths
BASE_DIR = Path(__file__).resolve().parent.parent.parent
config = Config(RepositoryEnv(BASE_DIR / '.env'))

# Security
SECRET_KEY = config('SECRET_KEY', default='django-insecure-dev-key-change-me')
DEBUG = config('DEBUG', default=False, cast=bool)
ALLOWED_HOSTS = config('ALLOWED_HOSTS', default='localhost,127.0.0.1', cast=Csv())

# Application definition
INSTALLED_APPS = [
    'django.contrib.admin',
    'django.contrib.auth',
    'django.contrib.contenttypes',
    'django.contrib.sessions',
    'django.contrib.messages',
    'django.contrib.staticfiles',

    
    # Third-party
    'rest_framework',
    'corsheaders',
    'django_q',  # Enabled for async blockchain anchoring (apps.audit.tasks). Requires PostgreSQL ORM broker; run `python manage.py migrate django_q`.
    
    # Local
    'apps.users',
    'apps.chamas',
    'apps.plans',
    'apps.payments',
    'apps.claims',
    'apps.audit',
]

MIDDLEWARE = [
    'django.middleware.security.SecurityMiddleware',
    'corsheaders.middleware.CorsMiddleware',
    'django.contrib.sessions.middleware.SessionMiddleware',
    'django.middleware.common.CommonMiddleware',
    'django.middleware.csrf.CsrfViewMiddleware',
    'django.contrib.auth.middleware.AuthenticationMiddleware',
    'django.contrib.messages.middleware.MessageMiddleware',
    'django.middleware.clickjacking.XFrameOptionsMiddleware',
]

ROOT_URLCONF = 'config.urls'

TEMPLATES = [
    {
        'BACKEND': 'django.template.backends.django.DjangoTemplates',
        'DIRS': [BASE_DIR / 'templates'],
        'APP_DIRS': True,
        'OPTIONS': {
            'context_processors': [
                'django.template.context_processors.debug',
                'django.template.context_processors.request',
                'django.contrib.auth.context_processors.auth',
                'django.contrib.messages.context_processors.messages',
            ],
        },
    },
]

WSGI_APPLICATION = 'config.wsgi.application'

# Database
DATABASE_URL = config('DATABASE_URL', default=None)

if DATABASE_URL:
    DATABASES = {
        'default': dj_database_url.config(
            default=DATABASE_URL,
            conn_max_age=600,
            conn_health_checks=True,
        )
    }
else:
    DATABASES = {
        'default': {
            'ENGINE': 'django.db.backends.postgresql',
            'NAME': config('DB_NAME', default='postgres'),
            'USER': config('DB_USER', default='postgres.arqvnmkhmebctsadjltz'),
            'PASSWORD': config('DB_PASSWORD', default='0741082524bima'),
            'HOST': config('DB_HOST', default='aws-0-eu-west-1.pooler.supabase.com'),
            'PORT': config('DB_PORT', default='5432'),
        }
    }

# Authentication
AUTH_USER_MODEL = 'users.User'

AUTH_PASSWORD_VALIDATORS = [
    {'NAME': 'django.contrib.auth.password_validation.UserAttributeSimilarityValidator'},
    {'NAME': 'django.contrib.auth.password_validation.MinimumLengthValidator'},
    {'NAME': 'django.contrib.auth.password_validation.CommonPasswordValidator'},
    {'NAME': 'django.contrib.auth.password_validation.NumericPasswordValidator'},
]


# Internationalization
LANGUAGE_CODE = 'en-us'
TIME_ZONE = 'Africa/Nairobi'
USE_I18N = True
USE_TZ = True

# Static and Media
STATIC_URL = '/static/'
STATIC_ROOT = BASE_DIR / 'staticfiles'
MEDIA_URL = '/media/'
MEDIA_ROOT = BASE_DIR / 'media'

# Default primary key field type
DEFAULT_AUTO_FIELD = 'django.db.models.BigAutoField'

LOGIN_URL = '/login/'
LOGIN_REDIRECT_URL = '/'

# REST Framework Configuration
REST_FRAMEWORK = {
    'DEFAULT_AUTHENTICATION_CLASSES': (
        'rest_framework.authentication.SessionAuthentication',
        'rest_framework_simplejwt.authentication.JWTAuthentication',
    ),
    'DEFAULT_PERMISSION_CLASSES': (
        'rest_framework.permissions.IsAuthenticated',
    ),
    'DEFAULT_PAGINATION_CLASS': 'rest_framework.pagination.PageNumberPagination',
    'PAGE_SIZE': 20,
    'DEFAULT_FILTER_BACKENDS': [
        'rest_framework.filters.SearchFilter',
        'rest_framework.filters.OrderingFilter',
    ],
}

# JWT Configuration
SIMPLE_JWT = {
    'ACCESS_TOKEN_LIFETIME': timedelta(
        hours=int(config('JWT_ACCESS_TOKEN_LIFETIME_HOURS', default=24))
    ),
    'REFRESH_TOKEN_LIFETIME': timedelta(
        days=int(config('JWT_REFRESH_TOKEN_LIFETIME_DAYS', default=7))
    ),
    'ALGORITHM': 'HS256',
    'SIGNING_KEY': SECRET_KEY,
    'VERIFYING_KEY': None,
    'AUTH_HEADER_TYPES': ('Bearer',),
    'USER_ID_FIELD': 'id',
    'USER_ID_CLAIM': 'user_id',
}

# CORS Configuration
CORS_ALLOWED_ORIGINS = config(
    'CORS_ALLOWED_ORIGINS',
    default='http://localhost:8000,http://127.0.0.1:8000',
    cast=Csv()
)
CORS_ALLOW_CREDENTIALS = True

# Django-Q Configuration (ORM Broker with PostgreSQL)
Q_CLUSTER = {
    'name': 'bima_afya',
    'workers': 4,
    'timeout': 500,
    'retry': 600,
    'queue_limit': 50,
    'bulk': 10,
    'orm': 'default',
    'catch_up': False,
}

# Safaricom Daraja Configuration
# Blockchain Anchoring (Polygon Amoy testnet — BimaRegistry contract)
# If any of these are unset, BlockchainAnchorService falls back to a
# simulated tx hash instead of raising, so the app runs fine without them.
POLYGON_AMOY_RPC_URL = config('POLYGON_AMOY_RPC_URL', default='https://rpc-amoy.polygon.technology')
BIMA_BORA_REGISTRY_ADDRESS = config('BIMA_BORA_REGISTRY_ADDRESS', default='')
OPERATOR_PRIVATE_KEY = config('OPERATOR_PRIVATE_KEY', default='')

DARAJA_CONSUMER_KEY = config('DARAJA_CONSUMER_KEY', default='')
DARAJA_CONSUMER_SECRET = config('DARAJA_CONSUMER_SECRET', default='')
DARAJA_SHORTCODE = config('DARAJA_SHORTCODE', default='174379')
DARAJA_PASSKEY = config('DARAJA_PASSKEY', default='')
DARAJA_CALLBACK_URL = config('DARAJA_CALLBACK_URL', default='')
DARAJA_ENV = config('DARAJA_ENV', default='sandbox')

# B2C (claim payout) settings.
#
# DARAJA_INITIATOR_NAME — the API operator username for B2C requests.
# 'testapi' is the standard sandbox initiator and works out of the box
# against the Daraja sandbox. In production this MUST be the real
# initiator/operator username issued on your Daraja portal (Go Live ->
# API operator), and it must be the same identity whose password you
# encrypt into DARAJA_SECURITY_CREDENTIAL below — a mismatch between
# the two is the most common cause of "The initiator information is
# invalid" errors from the B2C endpoint.
DARAJA_INITIATOR_NAME = config('DARAJA_INITIATOR_NAME', default='testapi')

# DARAJA_B2C_SHORTCODE — the organization shortcode B2C requests use
# as PartyA. In the Daraja SANDBOX this is deliberately a different
# test shortcode from DARAJA_SHORTCODE (which is the 174379 STK/C2B
# paybill) — B2C has its own test org shortcode (commonly in the
# 600xxx range) that's paired with the 'testapi' initiator and the
# SecurityCredential shown on the same Test Credentials page. Using
# 174379 for B2C is a common cause of a bare "400 Bad Request" with
# no other explanation. Defaults to DARAJA_SHORTCODE for backwards
# compatibility, but sandbox B2C almost always needs this overridden —
# check the Test Credentials page on the Daraja portal for the
# shortcode listed next to your B2C SecurityCredential.
DARAJA_B2C_SHORTCODE = config('DARAJA_B2C_SHORTCODE', default=DARAJA_SHORTCODE)

# DARAJA_SECURITY_CREDENTIAL — the RSA-encrypted initiator password
# Daraja expects on every B2C request. This is NOT the raw password:
# it's the initiator password encrypted against Safaricom's public
# certificate (PKCS1v15 padding), base64-encoded. Generate it with
# scripts/generate_security_credential.py and paste the output here
# (via .env) — see that script's docstring for the full walkthrough.
DARAJA_SECURITY_CREDENTIAL = config('DARAJA_SECURITY_CREDENTIAL', default='')

# Africa's Talking Configuration
AT_API_KEY = config('AT_API_KEY', default='')
AT_USERNAME = config('AT_USERNAME', default='sandbox')
AT_SENDER_ID = config('AT_SENDER_ID', default='BimaAfya')
# AT doesn't sign delivery report callbacks, so we verify authenticity via a
# shared-secret query param on the callback URL itself (the pattern AT's own
# docs recommend): .../sms/delivery/?key=<AT_CALLBACK_SECRET>
AT_CALLBACK_SECRET = config('AT_CALLBACK_SECRET', default='')

# Azure Blob Storage Configuration (commented for migration review)
# AZURE_ACCOUNT_NAME = config('AZURE_ACCOUNT_NAME', default='')
# AZURE_ACCOUNT_KEY = config('AZURE_ACCOUNT_KEY', default='')
# AZURE_CONTAINER = config('AZURE_CONTAINER', default='bima-afya-documents')
#
# USE_AZURE_STORAGE = AZURE_ACCOUNT_NAME and AZURE_ACCOUNT_KEY
#
# if USE_AZURE_STORAGE:
#     STORAGES = {
#         'default': {
#             'BACKEND': 'storages.backends.azure_storage.AzureStorage',
#             'OPTIONS': {
#                 'account_name': AZURE_ACCOUNT_NAME,
#                 'account_key': AZURE_ACCOUNT_KEY,
#                 'azure_container': AZURE_CONTAINER,
#             }
#         },
#         'staticfiles': {
#             'BACKEND': 'django.contrib.staticfiles.storage.StaticFilesStorage',
#         }
#     }
# else:
#     STORAGES = {
#         'default': {
#             'BACKEND': 'django.core.files.storage.FileSystemStorage',
#         },
#         'staticfiles': {
#             'BACKEND': 'django.contrib.staticfiles.storage.StaticFilesStorage',
#         }
#     }

# Current storage backend: local static files + app-managed Mongo Atlas GridFS service.
STORAGES = {
    'default': {
        'BACKEND': 'django.core.files.storage.FileSystemStorage',
    },
    'staticfiles': {
        'BACKEND': 'django.contrib.staticfiles.storage.StaticFilesStorage',
    }
}
# Email Configuration
EMAIL_BACKEND = config('EMAIL_BACKEND', default='django.core.mail.backends.console.EmailBackend')
EMAIL_HOST = config('EMAIL_HOST', default='localhost')
EMAIL_PORT = config('EMAIL_PORT', default=1025, cast=int)
EMAIL_USE_TLS = config('EMAIL_USE_TLS', default=False, cast=bool)
EMAIL_HOST_USER = config('EMAIL_HOST_USER', default='')
EMAIL_HOST_PASSWORD = config('EMAIL_HOST_PASSWORD', default='')
DEFAULT_FROM_EMAIL = config('DEFAULT_FROM_EMAIL', default='noreply@bimaafya.com')

# Logging Configuration
LOGGING = {
    'version': 1,
    'disable_existing_loggers': False,
    'formatters': {
        'verbose': {
            'format': '{levelname} {asctime} {module} {process:d} {thread:d} {message}',
            'style': '{',
        },
    },
    'handlers': {
        'console': {
            'class': 'logging.StreamHandler',
            'formatter': 'verbose',
        },
    },
    'root': {
        'handlers': ['console'],
        'level': 'INFO',
    },
}
