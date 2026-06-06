from django.apps import AppConfig


class UserConfig(AppConfig):
    default_auto_field = "django.db.models.BigAutoField"
    name = "users"
    verbose_name = "Users"
    
    def ready(self):
        """
        App fully load hone ke baad run hota hai.
        Signals yahan import karenge (baad mein add honge).
        """
        pass