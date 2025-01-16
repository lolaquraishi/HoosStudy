from django.apps import AppConfig

class HoosStudyAppConfig(AppConfig):
    default_auto_field = 'django.db.models.BigAutoField'
    name = 'hoos_study_app'

    def ready(self):
        import hoos_study_app.signals  # Import the signal logic
