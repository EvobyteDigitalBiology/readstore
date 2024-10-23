# readstore-basic/backend/settings/base.py

"""

Django basic settings for the backend.

"""

from pathlib import Path
from typing import List
import yaml

# Build paths inside the project like this: BASE_DIR / 'subdir'.
BASE_DIR = Path(__file__).resolve().parent.parent.parent
RS_CONFIG_PATH = BASE_DIR / "rs_config.yaml"
assert RS_CONFIG_PATH.exists(), f"rs_config.yaml not found at {RS_CONFIG_PATH}"

def load_rs_config():
    with open(RS_CONFIG_PATH, "r") as f:
        return yaml.safe_load(f)

RS_CONFIG = load_rs_config()

# Defines production or dev mode
DJANGO_SETTINGS_MODULE=RS_CONFIG['django']['django_settings_module']

# Application definition

INSTALLED_APPS = [
    "django.contrib.admin",
    "django.contrib.auth",
    "django.contrib.contenttypes",
    "django.contrib.sessions",
    "django.contrib.messages",
    "django.contrib.staticfiles",
    "rest_framework",
    "app",
]

MIDDLEWARE = [
    "django.middleware.security.SecurityMiddleware",
    "django.contrib.sessions.middleware.SessionMiddleware",
    "django.middleware.common.CommonMiddleware",
    "django.middleware.csrf.CsrfViewMiddleware",
    "django.contrib.auth.middleware.AuthenticationMiddleware",
    "django.contrib.messages.middleware.MessageMiddleware",
    "django.middleware.clickjacking.XFrameOptionsMiddleware",
]

ROOT_URLCONF = "backend.urls"

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
                "django.contrib.messages.context_processors.messages",
            ],
        },
    },
]

WSGI_APPLICATION = "backend.wsgi.application"

# Database
# https://docs.djangoproject.com/en/4.2/ref/settings/#databases

DATABASE_ROUTERS: List = []

REST_FRAMEWORK = {
    "DEFAULT_AUTHENTICATION_CLASSES": [
        "rest_framework.authentication.BasicAuthentication",
        "rest_framework_simplejwt.authentication.JWTAuthentication",
        "rest_framework.authentication.SessionAuthentication",
    ],
    # 'DEFAULT_PAGINATION_CLASS': 'rest_framework.pagination.PageNumberPagination',
    # 'PAGE_SIZE': 10,
}

# Password validation
# https://docs.djangoproject.com/en/4.2/ref/settings/#auth-password-validators

AUTH_PASSWORD_VALIDATORS = [
#     {
#         'NAME':
# 'django.contrib.auth.password_validation.UserAttributeSimilarityValidator',
#     },
#     {
#         'NAME':
# 'django.contrib.auth.password_validation.MinimumLengthValidator',
#     },
#     {

# 'NAME':
# 'django.contrib.auth.password_validation.CommonPasswordValidator',
#     },
#     {

# 'NAME':
# 'django.contrib.auth.password_validation.NumericPasswordValidator',
#     },
]

PASSWORD_HASHERS = [
    "django.contrib.auth.hashers.PBKDF2PasswordHasher",
    "django.contrib.auth.hashers.BCryptSHA256PasswordHasher",
    "django.contrib.auth.hashers.PBKDF2SHA1PasswordHasher",
    "django.contrib.auth.hashers.Argon2PasswordHasher",
    "django.contrib.auth.hashers.ScryptPasswordHasher",
]

# Internationalization
# https://docs.djangoproject.com/en/4.2/topics/i18n/

LANGUAGE_CODE = "en-us"
TIME_ZONE = "UTC"
USE_I18N = True
USE_TZ = True

# Static files (CSS, JavaScript, Images)
# https://docs.djangoproject.com/en/4.2/howto/static-files/

STATIC_URL = "static/"

# STATIC_ROOT = '/var/www/example.com/static/'

# Default primary key field type
# https://docs.djangoproject.com/en/4.2/ref/settings/#default-auto-field

DEFAULT_AUTO_FIELD = "django.db.models.BigAutoField"


# LOGGING
LOGGING = {
    "version": 1,
    "disable_existing_loggers": False,
    "handlers": {
        "file": {
            "level": "DEBUG",
            "class": "logging.FileHandler",
            "filename": RS_CONFIG['django']['logger_path'],
        },
    },
    "loggers": {
        "django": {
            "handlers": ["file"],
            "level": "DEBUG",
            "propagate": True,
        },
    },
}


# Non Django related config
VALID_FASTQ_EXTENSIONS = RS_CONFIG['global']['valid_fastq_extensions'].split(',')
VALID_READ1_SUFFIX = RS_CONFIG['global']['valid_read1_suffix'].split(',')
VALID_READ2_SUFFIX = RS_CONFIG['global']['valid_read2_suffix'].split(',')
VALID_INDEX1_SUFFIX = RS_CONFIG['global']['valid_index1_suffix'].split(',')
VALID_INDEX2_SUFFIX = RS_CONFIG['global']['valid_index2_suffix'].split(',')

FQ_QUEUE_NUM_WORKERS = RS_CONFIG['django']['fq_queue_num_workers']
FQ_QUEUE_MAX_SIZE = RS_CONFIG['django']['fq_queue_maxsize']