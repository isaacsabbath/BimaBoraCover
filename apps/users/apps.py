# For beginners: This file (apps/users/apps.py) contains part of the application logic.
# For beginners: Read this file from top to bottom to see what data it handles
# and which functions/classes other files can call.

"""
Apps configuration for users app.
"""

from django.apps import AppConfig


# For beginners: This class 'UsersConfig' groups related data and behavior
# so other parts of the app can use one structured object.
# For beginners: This class 'UsersConfig' groups related data and behavior
# so other parts of the app can use one structured object.
class UsersConfig(AppConfig):
    default_auto_field = 'django.db.models.BigAutoField'
    name = 'apps.users'
    verbose_name = 'Users'
    
    # For beginners: This function 'ready' performs one reusable task.
    # Other parts of the app call it to avoid duplicating logic.
    # For beginners: This function 'ready' performs one reusable task.
    # Other parts of the app call it to avoid duplicating logic.
    def ready(self):
        """Import signals when app is ready."""
        import apps.users.signals  # noqa
