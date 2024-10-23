# readstore-basic/backend/app/apps.py

from django.apps import AppConfig


class TempDjangoAppConfig(AppConfig):
    default_auto_field = 'django.db.models.BigAutoField'
    name = 'app'
