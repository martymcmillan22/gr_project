from django.apps import AppConfig


class PlatformCoreConfig(AppConfig):
    default_auto_field = "django.db.models.BigAutoField"
    name = "platform_core"

    def ready(self):
        from .unified_admin import configure_unified_admin

        configure_unified_admin()
