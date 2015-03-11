from django.conf import settings
#from oauth_tokens.models import AccessToken

from instagram.client import InstagramAPI
#from oauth_tokens.api import ApiAbstractBase, Singleton


__all__ = ['get_api', ]

INSTAGRAM_CLIENT_ID = getattr(settings, 'INSTAGRAM_CLIENT_ID', None)
#INSTAGRAM_CLIENT_SECRET = getattr(settings, 'OAUTH_TOKENS_INSTAGRAM_CLIENT_SECRET', None)
#INSTAGRAM_API_ACCESS_TOKEN = getattr(settings, 'INSTAGRAM_API_ACCESS_TOKEN', None)



def get_api(*args, **kwargs):
    api = InstagramAPI(client_id=INSTAGRAM_CLIENT_ID)
    return api
