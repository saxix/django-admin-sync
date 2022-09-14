import os

SECRET_KEY = "aaaaaaa"

ADMIN_SYNC_LOCAL_ADMIN_URL = ""
ADMIN_SYNC_REMOTE_ADMIN_URL = ""
ADMIN_SYNC_USE_REVERSION = True

if os.environ.get("ADMIN_SYNC_REMOTE"):
    SESSION_COOKIE_NAME = "remote"
    ADMIN_SYNC_REMOTE_SERVER = ""
    DATABASE_NAME = os.environ.get("DATABASE_NAME", "admin_sync.sqlite3")
else:
    SESSION_COOKIE_NAME = "local"
    ADMIN_SYNC_REMOTE_SERVER = os.environ.get(
        "ADMIN_SYNC_REMOTE_SERVER", "http://localhost:8001"
    )
    DATABASE_NAME = os.environ.get("DATABASE_NAME", "admin_sync.sqlite3")

DATABASES = {
    "default": {
        "ENGINE": "django.db.backends.sqlite3",
        "NAME": f"{SESSION_COOKIE_NAME}_{DATABASE_NAME}",
        "TEST": {
            "NAME": ":memory:",
        },
        "TEST_NAME": ":memory:",
        "HOST": "",
        "PORT": "",
        "ATOMIC_REQUESTS": True,
    }
}

DEBUG = True
TEMPLATE_DEBUG = DEBUG
USE_TZ = True
MIDDLEWARE = (
    "django.contrib.sessions.middleware.SessionMiddleware",
    "django.middleware.common.CommonMiddleware",
    "django.middleware.csrf.CsrfViewMiddleware",
    "django.contrib.auth.middleware.AuthenticationMiddleware",
    "django.contrib.messages.middleware.MessageMiddleware",
)
if DEBUG:
    AUTHENTICATION_BACKENDS = [
        "demoapp.backends.AnyUserBackend",
    ]
DEFAULT_AUTO_FIELD = 'django.db.models.AutoField'

TEMPLATES = [
    {
        "BACKEND": "django.template.backends.django.DjangoTemplates",
        "DIRS": [],
        "APP_DIRS": True,
        "OPTIONS": {
            "context_processors": [
                "django.contrib.messages.context_processors.messages",
                "django.contrib.auth.context_processors.auth",
                "django.template.context_processors.request",
            ]
        },
    },
]

ROOT_URLCONF = "demoapp.urls"
STATIC_URL = "/static/"

INSTALLED_APPS = [
    "django.contrib.auth",
    "django.contrib.contenttypes",
    "django.contrib.sessions",
    "django.contrib.messages",
    "django.contrib.staticfiles",
    # "django.contrib.admin",
    "reversion",
    "concurrency",
    "smart_admin.apps.SmartTemplateConfig",
    "smart_admin.apps.SmartConfig",
    "admin_extra_buttons",
    "admin_sync",
    "demoapp.apps.Config",
]
