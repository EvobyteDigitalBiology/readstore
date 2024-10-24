# readstore-basic/backend/settings/development.py

"""

Django dev settings for the backend.

"""

from datetime import timedelta
import os

from .base import *


# Load SECRET KEY
if not 'RS_KEY_PATH' in os.environ:
    raise ValueError("RS_KEY_PATH not found in environment variables")
else:
    RS_KEY_PATH = os.environ['RS_KEY_PATH']

assert os.path.exists(RS_KEY_PATH), f"rs_config.yaml not found at {RS_KEY_PATH}"

with open(RS_KEY_PATH, "r") as f:
    SECRET_KEY = f.read()


# Load config
if not 'RS_CONFIG_PATH' in os.environ:
    raise ValueError("RS_CONFIG_PATH not found in environment variables")
else:
    RS_CONFIG_PATH = os.environ['RS_CONFIG_PATH']

assert os.path.exists(RS_CONFIG_PATH), f"rs_config.yaml not found at {RS_CONFIG_PATH}"

with open(RS_CONFIG_PATH, "r") as f:
    rs_config = yaml.safe_load(f)



# SECURITY WARNING: don't run with debug turned on in production!
DEBUG = True
ALLOWED_HOSTS = rs_config['django']['allowed_hosts'].split(",")

# Can be used to switch production and test databases
DATABASES = {
    "default": {
        "ENGINE": "django.db.backends.sqlite3",
        "NAME": rs_config["django"]["db_path"],
    },
}

SIMPLE_JWT = {
    "ACCESS_TOKEN_LIFETIME": timedelta(seconds=rs_config["django"]["access_token_lifetime"]),
    "REFRESH_TOKEN_LIFETIME": timedelta(days=1),
    "ROTATE_REFRESH_TOKENS": False,
    "BLACKLIST_AFTER_ROTATION": False,
    "UPDATE_LAST_LOGIN": False,

    "ALGORITHM": "HS256",
    "SIGNING_KEY": SECRET_KEY,
    "VERIFYING_KEY": "",
    "AUDIENCE": None,
    "ISSUER": None,
    "JSON_ENCODER": None,
    "JWK_URL": None,
    "LEEWAY": 0,

    "AUTH_HEADER_TYPES": ("Bearer","JWT"),
    "AUTH_HEADER_NAME": "HTTP_AUTHORIZATION",
    "USER_ID_FIELD": "id",
    "USER_ID_CLAIM": "user_id",
    "USER_AUTHENTICATION_RULE":
"rest_framework_simplejwt.authentication.default_user_authentication_rule",

    "AUTH_TOKEN_CLASSES": ("rest_framework_simplejwt.tokens.AccessToken",),
    "TOKEN_TYPE_CLAIM": "token_type",
    "TOKEN_USER_CLASS": "rest_framework_simplejwt.models.TokenUser",

    "JTI_CLAIM": "jti",

    "SLIDING_TOKEN_REFRESH_EXP_CLAIM": "refresh_exp",
    "SLIDING_TOKEN_LIFETIME": timedelta(minutes=5),
    "SLIDING_TOKEN_REFRESH_LIFETIME": timedelta(days=1),

    "TOKEN_OBTAIN_SERIALIZER":
"rest_framework_simplejwt.serializers.TokenObtainPairSerializer",
    "TOKEN_REFRESH_SERIALIZER":
"rest_framework_simplejwt.serializers.TokenRefreshSerializer",
    "TOKEN_VERIFY_SERIALIZER":
"rest_framework_simplejwt.serializers.TokenVerifySerializer",
    "TOKEN_BLACKLIST_SERIALIZER":
"rest_framework_simplejwt.serializers.TokenBlacklistSerializer",
    "SLIDING_TOKEN_OBTAIN_SERIALIZER":
"rest_framework_simplejwt.serializers.TokenObtainSlidingSerializer",
    "SLIDING_TOKEN_REFRESH_SERIALIZER":
"rest_framework_simplejwt.serializers.TokenRefreshSlidingSerializer",
}
