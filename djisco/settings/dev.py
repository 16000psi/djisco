from .base import *  # noqa: F401, F403

DEBUG = True

INSTALLED_APPS.append(  # noqa: F405
    "debug_toolbar",
)

MIDDLEWARE.insert(0, "debug_toolbar.middleware.DebugToolbarMiddleware")  # noqa: F405


INTERNAL_IPS = [
    "127.0.0.1",
]
