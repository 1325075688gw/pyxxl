from django.conf import settings

from .client import GConfClient

gconf_client = GConfClient(**settings.GCONF)
gconf_decorator = gconf_client.decorator()
