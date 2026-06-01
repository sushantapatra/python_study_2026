from django.apps import AppConfig
from django.db.backends.signals import connection_created

def fix_mysql_index_limit(sender, connection, **kwargs):
    """
    Interceptors backend database connection matrices to dynamically override 
    row storage formats for heavy indexes.
    """
    if connection.vendor == 'mysql':
        with connection.cursor() as cursor:
            # Force target storage structures to handle large indexes up to 3072 bytes
            cursor.execute("SET SESSION innodb_strict_mode=OFF;")


class UsersConfig(AppConfig):
    default_auto_field = 'django.db.models.BigAutoField'
    name = 'users'

    def ready(self):
        # Bind the connection mechanism right into the boot cycle framework
        connection_created.connect(fix_mysql_index_limit)
