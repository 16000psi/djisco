import os

from .base import *  # noqa: F401, F403

# DEBUG = False
DEBUG = True

# ALLOWED_HOSTS.append(".davesmith.io")  # noqa: F405
ALLOWED_HOSTS.append("*")  # noqa: F405

DATABASES = {
    "default": {
        "ENGINE": "django.db.backends.postgresql",
        "NAME": os.getenv("POSTGRES_DB"),
        "USER": os.getenv("POSTGRES_USER"),
        "PASSWORD": os.getenv("POSTGRES_PASSWORD"),
        "HOST": "db",
        "PORT": "5432",
    }
}

STATIC_ROOT = "/app/static/"

SECRET_KEY = os.getenv("DJANGO_SECRET_KEY")
