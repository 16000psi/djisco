import os

from dotenv import load_dotenv

from .base import *  # noqa: F401, F403

load_dotenv()
DEBUG = True

INSTALLED_APPS.append(  # noqa: F405
    "debug_toolbar",
)

MIDDLEWARE.insert(0, "debug_toolbar.middleware.DebugToolbarMiddleware")  # noqa: F405


INTERNAL_IPS = [
    "127.0.0.1",
]

ALLOWED_HOSTS.append("*")  # noqa: F405

DATABASES = {
    "default": {
        "ENGINE": "django.db.backends.postgresql_psycopg2",
        "NAME": os.getenv("POSTGRES_DB_DEVELOPMENT"),
        "USER": os.getenv("POSTGRES_USER_DEVELOPMENT"),
        "PASSWORD": os.getenv("POSTGRES_PASSWORD_DEVELOPMENT"),
        "HOST": "localhost",
        "PORT": "5432",
    }
}
