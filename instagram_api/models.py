# -*- coding: utf-8 -*-
from datetime import datetime
import logging
import re

from django.db import models
from django.db.models.fields import FieldDoesNotExist
from django.db.models.related import RelatedObject
from django.utils import timezone
import requests
from instagram.helper import timestamp_to_datetime
from instagram.models import ApiModel
from m2m_history.fields import ManyToManyHistoryField
from . import fields
from .api import get_api

__all__ = ['User', 'Media', 'Comment', 'InstagramContentError', 'InstagramModel', 'InstagramManager', 'UserManager']

log = logging.getLogger('instagram_api')


class InstagramContentError(Exception):
    pass


class InstagramManager(models.Manager):
    """
    Instagram Manager for RESTful CRUD operations
    """

    def __init__(self, methods=None, remote_pk=None, *args, **kwargs):
        self.api = get_api()

        if methods and len(methods.items()) < 1:
            raise ValueError('Argument methods must contains at least 1 specified method')

        self.methods = methods or {}
        self.remote_pk = remote_pk or ('id',)
        if not isinstance(self.remote_pk, tuple):
            self.remote_pk = (self.remote_pk,)

        super(InstagramManager, self).__init__(*args, **kwargs)

    def get_or_create_from_instance(self, instance):

        remote_pk_dict = {}
        for field_name in self.remote_pk:
            remote_pk_dict[field_name] = getattr(instance, field_name)

        try:
            old_instance = self.model.objects.get(**remote_pk_dict)
            instance._substitute(old_instance)
            instance.save()
        except self.model.DoesNotExist:
            instance.save()
            log.debug('Fetch and create new object %s with remote pk %s' % (self.model, remote_pk_dict))

        return instance

    def api_call(self, method, *args, **kwargs):
        if method in self.methods:
            method = self.methods[method]
        return getattr(self.api, method)(*args, **kwargs)

    def fetch(self, *args, **kwargs):
        """
        Retrieve and save object to local DB
        """
        result = self.get(*args, **kwargs)
        if isinstance(result, list):
            return [self.get_or_create_from_instance(instance) for instance in result]
        else:
            return self.get_or_create_from_instance(result)

    def get(self, *args, **kwargs):
        """
        Retrieve objects from remote server
        """
        response = self.api_call('get', *args, **kwargs)

        extra_fields = kwargs.pop('extra_fields', {})
        extra_fields['fetched'] = timezone.now()
        return self.parse_response(response, extra_fields)

    def parse_response(self, response, extra_fields=None):
        if isinstance(response, (list, tuple)):
            return self.parse_response_list(response, extra_fields)
        elif isinstance(response, ApiModel):
            return self.parse_response_object(response, extra_fields)
        else:
            raise InstagramContentError('Instagram response should be list or dict, not %s' % response)

    def parse_response_object(self, resource, extra_fields=None):

        instance = self.model()
        # important to do it before calling parse method
        if extra_fields:
            instance.__dict__.update(extra_fields)
        instance._response = resource.__dict__ if isinstance(resource, ApiModel) else resource
        instance.parse()

        return instance

    def parse_response_list(self, response_list, extra_fields=None):

        instances = []
        for response in response_list:

            if not isinstance(response, ApiModel):
                log.error("Resource %s is not dictionary" % response)
                continue

            instance = self.parse_response_object(response, extra_fields)
            instances += [instance]

        return instances


class InstagramModel(models.Model):
    objects = models.Manager()

    class Meta:
        abstract = True

    def __init__(self, *args, **kwargs):
        super(InstagramModel, self).__init__(*args, **kwargs)

        # different lists for saving related objects
        self._external_links_post_save = []
        self._foreignkeys_pre_save = []
        self._external_links_to_add = []

    def _substitute(self, old_instance):
        """
        Substitute new user with old one while updating in method Manager.get_or_create_from_instance()
        Can be overrided in child models
        """
        self.pk = old_instance.pk
        # self.created_at = old_instance.created_at

    def save(self, *args, **kwargs):
        """
        Save all related instances before or after current instance
        """
        for field, instance in self._foreignkeys_pre_save:
            instance = instance.__class__.remote.get_or_create_from_instance(instance)
            setattr(self, field, instance)
        self._foreignkeys_pre_save = []

        super(InstagramModel, self).save(*args, **kwargs)

    def parse(self):
        """
        Parse API response and define fields with values
        """
        for key, value in self._response.items():
            if key == '_api':
                continue

            try:
                field, model, direct, m2m = self._meta.get_field_by_name(key)
            except FieldDoesNotExist:
                log.debug('Field with name "%s" doesn\'t exist in the model %s' % (key, type(self)))
                continue

            if isinstance(field, RelatedObject) and value:
                # for item in value:
                # rel_instance = field.model.remote.parse_response_object(item)
                # self._external_links_post_save += [(field.field.name, rel_instance)]
                pass
            else:
                if isinstance(field, (models.BooleanField)):
                    value = bool(value)

                elif isinstance(field, (models.OneToOneField, models.ForeignKey)) and value:
                    rel_instance = field.rel.to.remote.parse_response_object(value)
                    value = rel_instance
                    if isinstance(field, models.ForeignKey):
                        self._foreignkeys_pre_save += [(key, rel_instance)]

                elif isinstance(field, (fields.CommaSeparatedCharField,
                                        models.CommaSeparatedIntegerField)) and isinstance(value, list):
                    value = ','.join([unicode(v) for v in value])

                elif isinstance(field, (models.CharField, models.TextField)) and value:
                    if isinstance(value, (str, unicode)):
                        value = value.strip()

                setattr(self, key, value)


class InstagramBaseModel(InstagramModel):
    _tweepy_model = None
    _response = None

    fetched = models.DateTimeField(u'Fetched', null=True, blank=True)

    class Meta:
        abstract = True

    def get_url(self):
        return 'https://instagram.com/%s' % self.slug


class UserManager(InstagramManager):

    def fetch_by_slug(self, *args, **kwargs):
        result = self.get_by_slug(*args, **kwargs)
        return self.get_or_create_from_instance(result)

    def get_by_url(self, url):
        """
        Return object by url
        """
        m = re.findall(r'(?:https?://)?(?:www\.)?instagram\.com/([^/]+)/?', url)
        if not len(m):
            raise ValueError("Url should be started with https://instagram.com/")

        return self.get_by_slug(m[0])

    def get_by_slug(self, slug):
        """
        Return existed User by slug or new intance with empty pk
        """
        users = self.search(slug, count=1)
        for user in users:
            if user.username == slug:
                return self.get(user.id)
        raise ValueError("No users found for the name %s" % slug)

    def search(self, q, *args, **kwargs):
        kwargs['q'] = q
        response = self.api_call('search', *args, **kwargs)

        extra_fields = kwargs.pop('extra_fields', {})
        extra_fields['fetched'] = timezone.now()

        return self.parse_response_list(response, extra_fields)

    def fetch_followers_for_user(self, user, all=False, next_url=None, count=50, _extra_fields=None):
        if not _extra_fields:
            _extra_fields = {}
            _extra_fields['fetched'] = timezone.now()

        if next_url:
            url = next_url
            r = requests.get(url)
        else:
            url = 'https://api.instagram.com/v1/users/%(user_id)s/followed-by' % {'user_id': user.id}
            r = requests.get(url, params={'client_id': self.api.client_id})  #

        json = r.json()
        next_url = json['pagination'].get('next_url', None)

        instances = []
        for response in json['data']:
            instance = self.parse_response_object(response, _extra_fields)
            instance = self.get_or_create_from_instance(instance)
            instances.append(instance)
            user.followers.add(instance)

        if all:
            if next_url:
                return self.fetch_followers_for_user(user, all=True, next_url=next_url, _extra_fields=_extra_fields)
            else:
                return user.followers.all()
        else:
            return instances

    def fetch_media_likes(self, media):
        # TODO: get all likes
        # https://instagram.com/developer/endpoints/likes/#get_media_likes
        # no pagination to get all likes
        # http://stackoverflow.com/questions/20478485/get-a-list-of-users-who-have-liked-a-media-not-working-anymore

        extra_fields = {}
        extra_fields['fetched'] = timezone.now()

        # users
        response = self.api.media_likes(media.remote_id)
        result = self.parse_response(response, extra_fields)

        for instance in result:
            i = self.get_or_create_from_instance(instance)
            media.likes_users.add(i)

        return media.likes_users.all()


class User(InstagramBaseModel):
    id = models.BigIntegerField(primary_key=True)
    username = models.CharField(max_length=50, unique=True)
    full_name = models.CharField(max_length=255)
    bio = models.CharField("BIO", max_length=255)

    profile_picture = models.URLField(max_length=300)
    website = models.URLField(max_length=300)

    followers_count = models.PositiveIntegerField(null=True)
    media_count = models.PositiveIntegerField(null=True)

    followers = ManyToManyHistoryField('User', versions=True)

    objects = models.Manager()
    remote = UserManager(methods={
        'get': 'user',
        'search': 'user_search',
    })

    @property
    def slug(self):
        return self.username

    def __unicode__(self):
        return self.full_name

    @property
    def instagram_link(self):
        return u'https://instagram.com/%s/' % self.username

    def parse(self):
        if isinstance(self._response, dict) and 'counts' in self._response:
            self._response['followers_count'] = self._response['counts']['followed_by']
            self._response['media_count'] = self._response['counts']['media']

        super(User, self).parse()

    def fetch_followers(self, **kwargs):
        return User.remote.fetch_followers_for_user(self, **kwargs)

    def fetch_recent_media(self, **kwargs):
        return Media.remote.fetch_user_recent_media(self, **kwargs)


class MediaManager(InstagramManager):
    def fetch_user_recent_media(self, user, all=False, next_url=None, count=20, _extra_fields=None):
        if not _extra_fields:
            _extra_fields = {}
            _extra_fields['fetched'] = timezone.now()
            _extra_fields['user'] = user
            _extra_fields['user_id'] = user.id

        if next_url:
            url = next_url
            r = requests.get(url)
        else:
            url = 'https://api.instagram.com/v1/users/%(user_id)s/media/recent/' % {'user_id': user.id}
            r = requests.get(url, params={'client_id': self.api.client_id})  #

        json = r.json()
        next_url = json['pagination'].get('next_url', None)

        instances = []
        for response in json['data']:
            instance = self.parse_response_object(response, _extra_fields)
            instance = self.get_or_create_from_instance(instance)
            instances.append(instance)

        if all:
            if next_url:
                return self.fetch_user_recent_media(user, all=True, next_url=next_url, _extra_fields=_extra_fields)
            else:
                return user.media_feed.all()
        else:
            return instances


class Media(InstagramBaseModel):
    remote_id = models.CharField(max_length=100, unique=True)
    caption = models.CharField(max_length=1000, blank=True)
    link = models.URLField(max_length=300)

    created_time = models.DateTimeField()

    comments_count = models.PositiveIntegerField(null=True)
    likes_count = models.PositiveIntegerField(null=True)

    user = models.ForeignKey(User, related_name="media_feed")
    likes_users = ManyToManyHistoryField('User', related_name="likes_media")

    remote = MediaManager(remote_pk=('remote_id',), methods={
        'get': 'media',
    })

    @property
    def slug(self):
        return self.link

    def __unicode__(self):
        return self.caption

    def parse(self):
        self._response['remote_id'] = self._response.pop('id')

        if not isinstance(self._response['created_time'], datetime):
            self._response['created_time'] = timestamp_to_datetime(self._response['created_time'])

        if 'comment_count' in self._response:
            self._response['comments_count'] = self._response.pop('comment_count')
        elif 'comments' in self._response:
            self._response['comments_count'] = self._response.pop('comments')['count']

        if 'like_count' in self._response:
            self._response['likes_count'] = self._response.pop('like_count')
        elif 'likes' in self._response:
            self._response['likes_count'] = self._response.pop('likes')['count']

        if isinstance(self._response['caption'], ApiModel):
            self._response['caption'] = self._response['caption'].text
        elif isinstance(self._response['caption'], dict):
            self._response['caption'] = self._response['caption']['text']

        super(Media, self).parse()

    def fetch_comments(self):
        return Comment.remote.fetch_media_comments(self)

    def fetch_likes(self):
        return User.remote.fetch_media_likes(self)

    def save(self, *args, **kwargs):
        if self.caption is None:
            self.caption = ""

        super(Media, self).save(*args, **kwargs)


class CommentManager(InstagramManager):
    def fetch_media_comments(self, media):
        # comments
        response = self.api.media_comments(media.remote_id)

        extra_fields = {}
        extra_fields['fetched'] = timezone.now()
        extra_fields['media_id'] = media.id
        extra_fields['owner_id'] = media.user_id

        result = self.parse_response(response, extra_fields)
        return [self.get_or_create_from_instance(instance) for instance in result]


class Comment(InstagramBaseModel):
    owner = models.ForeignKey(User, related_name='media_comments')
    user = models.ForeignKey(User, related_name='comments')
    media = models.ForeignKey(Media, related_name="comments")

    id = models.BigIntegerField(primary_key=True)
    text = models.TextField()
    created_time = models.DateTimeField()

    remote = CommentManager()

    @property
    def slug(self):
        return self.media.link

    def parse(self):
        self._response['created_time'] = self._response.pop('created_at')
        super(Comment, self).parse()
