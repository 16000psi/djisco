import os
from dotenv import load_dotenv

from .base import *  # noqa: F401, F403

load_dotenv()

DEBUG = False

ALLOWED_HOSTS.append("www.djisco.davesmith.io")  # noqa: F405
ALLOWED_HOSTS.append("djisco.davesmith.io")  # noqa: F405


DATABASES = {
    "default": {
        "ENGINE": "django.db.backends.postgresql_psycopg2",
        "NAME": os.getenv("POSTGRES_DB"),
        "USER": os.getenv("POSTGRES_USER"),
        "PASSWORD": os.getenv("POSTGRES_PASSWORD"),
        "HOST": "localhost",
        "PORT": "5432",
    }
}

STATIC_ROOT = os.getenv("DJANGO_STATIC_ROOT")  # noqa: F405

SECRET_KEY = os.getenv("DJANGO_SECRET_KEY")

LOGGING = {
    "version": 1,
    "disable_existing_loggers": False,
    "handlers": {
        "console": {
            "class": "logging.StreamHandler",
        },
    },
    "loggers": {
        "django": {
            "handlers": ["console"],
            "level": "INFO",
        },
    },
}
