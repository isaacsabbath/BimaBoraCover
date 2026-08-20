# For beginners: This file (apps/plans/apps.py) contains part of the application logic.
# For beginners: Read this file from top to bottom to see what data it handles
# and which functions/classes other files can call.

"""
Apps configuration for plans app.
"""

from django.apps import AppConfig


# For beginners: This class 'PlansConfig' groups related data and behavior
# so other parts of the app can use one structured object.
# For beginners: This class 'PlansConfig' groups related data and behavior
# so other parts of the app can use one structured object.
class PlansConfig(AppConfig):
    default_auto_field = 'django.db.models.BigAutoField'
    name = 'apps.plans'
    verbose_name = 'Insurance Plans'
