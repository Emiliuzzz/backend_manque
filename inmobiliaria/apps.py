from django.apps import AppConfig


class InmobiliariaConfig(AppConfig):
    default_auto_field = 'django.db.models.BigAutoField'
    name = 'inmobiliaria'

    def ready(self):
        try:
            import inmobiliaria.signals  
        except Exception:
            pass