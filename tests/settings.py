import os

SECRET_KEY = "SOME_SUPER_SECRET"

BASE_DIR = os.path.dirname(os.path.dirname(os.path.abspath(__file__)))

INSTALLED_APPS = [
    "django.contrib.auth",
    "django.contrib.admin",  # for django admin pages
    "django.contrib.messages",  # for django admin pages
    "django.contrib.contenttypes",
    "django.contrib.sessions",
    "django.contrib.staticfiles",
    "tests"
]

MIDDLEWARE = [
    "django.middleware.security.SecurityMiddleware",
    "django.contrib.sessions.middleware.SessionMiddleware",
    "django.contrib.auth.middleware.AuthenticationMiddleware",
    "django.contrib.messages.middleware.MessageMiddleware",  # for django admin pages
]

STATIC_URL = "static/"


TEMPLATES = [
    {
        "BACKEND": "django.template.backends.django.DjangoTemplates",
        "DIRS": [],
        "APP_DIRS": True,
        "OPTIONS": {
            "context_processors": [
                "django.template.context_processors.debug",
                "django.template.context_processors.request",
                "django.contrib.auth.context_processors.auth",
                "django.contrib.messages.context_processors.messages",  # for django admin pages
            ],
        },
    },
]


DATABASES = {"default": {'ENGINE': 'django.db.backends.sqlite3',
                         'NAME': os.path.join(BASE_DIR, 'db.sqlite3'), }}

DEBUG = True

ROOT_URLCONF = "tests.urls"
