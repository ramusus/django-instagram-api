import logging
from time import sleep

from django.conf import settings
from instagram import InstagramAPIError as InstagramError
from instagram.client import InstagramAPI
from social_api.api import ApiAbstractBase, Singleton

__all__ = ['get_api', ]

CLIENT_ID = getattr(settings, 'SOCIAL_API_INSTAGRAM_CLIENT_ID')
CLIENT_SECRET = getattr(settings, 'SOCIAL_API_INSTAGRAM_CLIENT_SECRET')

log = logging.getLogger('instagram_api')


@property
def code(self):
    return self.status_code


InstagramError.code = code


class InstagramApi(ApiAbstractBase):
    __metaclass__ = Singleton

    provider = 'instagram'
    error_class = InstagramError

    def get_api(self, token):

        context = getattr(settings, 'SOCIAL_API_CALL_CONTEXT', None)
        if context and self.provider in context and context[self.provider].get('use_client_id', False) is True:
            kwargs = {'client_id': CLIENT_ID}
        else:
            kwargs = {'access_token': token, 'client_secret': CLIENT_SECRET}

        return InstagramAPI(**kwargs)

    def get_api_response(self, *args, **kwargs):
        return getattr(self.api, self.method)(*args, **kwargs)

    def handle_error_code_400(self, e, *args, **kwargs):
        # OAuthAccessTokenException-The access_token provided is invalid.
        if e.error_type == 'OAuthAccessTokenException':
            self.used_access_tokens += [self.api.access_token]
            return self.repeat_call(*args, **kwargs)
        raise e

    def handle_error_code_429(self, e, *args, **kwargs):
        # Rate limited-Your client is making too many request per second
        return self.handle_rate_limit_error(e, *args, **kwargs)

    def handle_error_code_503(self, e, *args, **kwargs):
        return self.repeat_call(*args, **kwargs)

    def handle_rate_limit_error(self, e, *args, **kwargs):
        self.used_access_tokens += [self.api.access_token]
        if len(self.used_access_tokens) == len(self.tokens):
            log.warning("All access tokens are rate limited, need to wait 600 sec")
            sleep(600)
            self.used_access_tokens = []
        return self.repeat_call(*args, **kwargs)


def api_call(*args, **kwargs):
    api = InstagramApi()
    api.used_access_tokens = []
    return api.call(*args, **kwargs)
