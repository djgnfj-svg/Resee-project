from django.apps import AppConfig


class AlertsConfig(AppConfig):
    default_auto_field = 'django.db.models.BigAutoField'
    name = 'alerts'
    verbose_name = 'Alert System'
    
    def ready(self):
        """Import signal handlers when the app is ready"""
        import alerts.signals