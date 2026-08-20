# For beginners: This file (apps/payments/apps.py) contains part of the application logic.
# For beginners: Read this file from top to bottom to see what data it handles
# and which functions/classes other files can call.

"""
Apps configuration for payments app.
"""

from django.apps import AppConfig


# For beginners: This class 'PaymentsConfig' groups related data and behavior
# so other parts of the app can use one structured object.
# For beginners: This class 'PaymentsConfig' groups related data and behavior
# so other parts of the app can use one structured object.
class PaymentsConfig(AppConfig):
    default_auto_field = 'django.db.models.BigAutoField'
    name = 'apps.payments'
    verbose_name = 'Payments'
