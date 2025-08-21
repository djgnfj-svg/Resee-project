from django.apps import AppConfig


class BusinessIntelligenceConfig(AppConfig):
    default_auto_field = 'django.db.models.BigAutoField'
    name = 'business_intelligence'
    verbose_name = 'Business Intelligence'
    
    def ready(self):
        # Import signals if any are defined
        try:
            import business_intelligence.signals  # noqa
        except ImportError:
            pass