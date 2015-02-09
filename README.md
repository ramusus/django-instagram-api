# Django Instagram API

[![Build Status](https://travis-ci.org/ramusus/django-instagram-api.png?branch=master)](https://travis-ci.org/ramusus/django-instagram-api) [![Coverage Status](https://coveralls.io/repos/ramusus/django-instagram-api/badge.png?branch=master)](https://coveralls.io/r/ramusus/django-instagram-api)

Application for interacting with Instagram API objects using Django model interface

## Installation

    pip install django-instagram-api

Add into `settings.py` lines:

    INSTALLED_APPS = (
        ...
        'oauth_tokens',
        'm2m_history',
        'taggit',
        'instagram_api',
    )

    # oauth-tokens settings
    OAUTH_TOKENS_HISTORY = True                                        # to keep in DB expired access tokens
    OAUTH_TOKENS_INSTAGRAM_CLIENT_ID = ''                                # application ID
    OAUTH_TOKENS_INSTAGRAM_CLIENT_SECRET = ''                            # application secret key
    OAUTH_TOKENS_INSTAGRAM_USERNAME = ''                                 # user login
    OAUTH_TOKENS_INSTAGRAM_PASSWORD = ''                                 # user password

## Usage examples

### Simple API request

...
