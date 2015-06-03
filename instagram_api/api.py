import random
import logging
from time import sleep

from django.conf import settings

from instagram.client import InstagramAPI
from instagram import InstagramAPIError as InstagramError
from oauth_tokens.api import ApiAbstractBase, Singleton


__all__ = ['get_api', ]

CLIENT_IDS = getattr(settings, 'INSTAGRAM_API_CLIENT_IDS', [])

log = logging.getLogger('instagram_api')


@property
def code(self):
    return self.status_code


InstagramError.code = code


class InstagramApi(ApiAbstractBase):

    __metaclass__ = Singleton

    provider = 'instagram'
    error_class = InstagramError

    def get_token(self, *args, **kwargs):
        pass

    def get_api(self, token):
        client_id = random.choice(list(set(CLIENT_IDS).difference(set(self.used_access_tokens))))
        return InstagramAPI(client_id=client_id)

    def get_api_response(self, *args, **kwargs):
        return getattr(self.api, self.method)(*args, **kwargs)

    def log_and_raise(self, e, *args, **kwargs):
        self.logger.error("Error '%s'. Method %s, args: %s, kwargs: %s, recursion count: %d" % (
            e, self.method, args, kwargs, self.recursion_count))
        raise e

    def handle_error_code_429(self, e, *args, **kwargs):
        # Rate limited-Your client is making too many request per second
        return self.handle_rate_limit_error(e, *args, **kwargs)

    def handle_error_code_503(self, e, *args, **kwargs):
        # Rate limited-Your client is making too many request per second
        return self.handle_rate_limit_error(e, *args, **kwargs)

    def handle_rate_limit_error(self, e, *args, **kwargs):
        self.used_access_tokens += [self.api.client_id]
        if len(self.used_access_tokens) == len(CLIENT_IDS):
            log.warning("All client ids are rate limited, wait for 1 hour")
            sleep(3600)
            self.used_access_tokens = []
        return self.repeat_call(*args, **kwargs)


def api_call(*args, **kwargs):
    api = InstagramApi()
    return api.call(*args, **kwargs)
