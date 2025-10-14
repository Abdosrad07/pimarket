from django.apps import AppConfig


class MessagingConfig(AppConfig):
    default_auto_field = 'django.db.models.BigAutoField'
    name = 'apps.messaging'
    verbose_name = 'Système de Messagerie'
    
    def ready(self):
        """
        Méthode appelée lorsque l'application est prête
        Importe les signaux et autres configurations
        """
        # Importer les signaux
        from . import signals
        
        # Vous pouvez ajouter d'autres initialisations ici
        # Par exemple : configuration de tâches périodiques, etc.