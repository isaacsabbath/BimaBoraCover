#!/usr/bin/env python
# For beginners: This file (manage.py) contains part of the application logic.
# For beginners: Read this file from top to bottom to see what data it handles
# and which functions/classes other files can call.

"""Django's command-line utility for administrative tasks."""
import os
import sys


# For beginners: This function 'main' performs one reusable task.
# Other parts of the app call it to avoid duplicating logic.
# For beginners: This function 'main' performs one reusable task.
# Other parts of the app call it to avoid duplicating logic.
def main():
    """Run administrative tasks."""
    os.environ.setdefault('DJANGO_SETTINGS_MODULE', 'config.settings.local')
    try:
        from django.core.management import execute_from_command_line
    except ImportError as exc:
        raise ImportError(
            "Couldn't import Django. Are you sure it's installed and "
            "available on your PYTHONPATH environment variable? Did you "
            "forget to activate a virtual environment?"
        ) from exc
    execute_from_command_line(sys.argv)


if __name__ == '__main__':
    main()
