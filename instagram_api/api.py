from django.conf import settings
from instagram.client import InstagramAPI

__all__ = ['get_api', ]

INSTAGRAM_CLIENT_ID = getattr(settings, 'OAUTH_TOKENS_INSTAGRAM_CLIENT_ID', None)
INSTAGRAM_CLIENT_SECRET = getattr(settings, 'OAUTH_TOKENS_INSTAGRAM_CLIENT_SECRET', None)



def get_api(*args, **kwargs):
    api = InstagramAPI(client_id=INSTAGRAM_CLIENT_ID, client_secret=INSTAGRAM_CLIENT_SECRET)
    #return api.call(*args, **kwargs)
    return api
