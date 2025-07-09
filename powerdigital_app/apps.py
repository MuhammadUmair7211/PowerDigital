from django.apps import AppConfig


class PowerdigitalAppConfig(AppConfig):
    default_auto_field = 'django.db.models.BigAutoField'
    name = 'powerdigital_app'

    def ready(self):
        import powerdigital_app.signals
