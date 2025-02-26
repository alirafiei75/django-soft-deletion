# tests/test_settings.py
DEBUG = True

DATABASES = {
    "default": {
        "ENGINE": "django.db.backends.sqlite3",
        "NAME": ":memory:",  # Use in-memory DB for faster tests
    }
}

INSTALLED_APPS = [
    "django.contrib.auth",
    "django.contrib.contenttypes",
]

USE_TZ = True
TIME_ZONE = "UTC"

SECRET_KEY = "test-secret-key"

DEFAULT_AUTO_FIELD = "django.db.models.BigAutoField"
