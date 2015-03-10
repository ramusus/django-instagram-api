# -*- coding: utf-8 -*-
from django.db import models
from django.db.models.fields import FieldDoesNotExist
from django.db.models.related import RelatedObject
from django.utils import timezone
from django.utils.translation import ugettext as _
import logging
import re

from instagram.models import ApiModel
from m2m_history.fields import ManyToManyHistoryField

from . import fields
from .api import get_api
from .decorators import fetch_all


#from . import fields
#from .parser import get_replies
#api = get_api()

__all__ = ['User', 'Status', 'InstagramContentError', 'InstagramModel', 'InstagramManager', 'UserManager']

log = logging.getLogger('instagram_api')


class InstagramContentError(Exception):
    pass


class InstagramManager(models.Manager):

    '''
    Instagram Manager for RESTful CRUD operations
    '''

    def __init__(self, methods=None, remote_pk=None, *args, **kwargs):
        self.api = get_api()

        if methods and len(methods.items()) < 1:
            raise ValueError('Argument methods must contains at least 1 specified method')

        self.methods = methods or {}
        self.remote_pk = remote_pk or ('id',)
        if not isinstance(self.remote_pk, tuple):
            self.remote_pk = (self.remote_pk,)

        super(InstagramManager, self).__init__(*args, **kwargs)

    def get_by_url(self, url):
        '''
        Return object by url
        '''
        m = re.findall(r'(?:https?://)?(?:www\.)?instagram\.com/([^/]+)/?', url)
        if not len(m):
            raise ValueError("Url should be started with https://instagram.com/")

        return self.get_by_slug(m[0])

    def get_by_slug(self, slug):
        '''
        Return object by slug
        '''
        # TODO: change to self.get method
        return self.model.remote.fetch(slug)

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

#    def get_or_create_from_resource(self, resource):
#
#        instance = self.model()
#        instance.parse(dict(resource))
#
#        return self.get_or_create_from_instance(instance)

    def api_call(self, method, *args, **kwargs):
        if method in self.methods:
            method = self.methods[method]
        return getattr(self.api, method)(*args, **kwargs)

    def fetch(self, *args, **kwargs):
        '''
        Retrieve and save object to local DB
        '''
        result = self.get(*args, **kwargs)
        if isinstance(result, list):
            return [self.get_or_create_from_instance(instance) for instance in result]
        else:
            return self.get_or_create_from_instance(result)

    def get(self, *args, **kwargs):
        '''
        Retrieve objects from remote server
        '''
        extra_fields = kwargs.pop('extra_fields', {})
        extra_fields['fetched'] = timezone.now()
        response = self.api_call('get', *args, **kwargs)

        return self.parse_response(response, extra_fields)

    def parse_response(self, response, extra_fields=None):
        # if response is None:
        #     return []
        # el
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
        instance.set_tweepy(resource)
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


class UserManager(InstagramManager):

    def get_followers_ids_for_user(self, user, all=False, count=5000, **kwargs):
        # https://dev.instagram.com/docs/api/1.1/get/followers/ids
        if all:
            cursor = tweepy.Cursor(user.tweepy._api.followers_ids, id=user.pk, count=count)
            return list(cursor.items())
        else:
            raise NotImplementedError("This method implemented only with argument all=True")

    def fetch_followers_for_user(self, user, all=False, count=200, **kwargs):
        # https://dev.instagram.com/docs/api/1.1/get/followers/list
        # in docs default count is 20, but maximum is 200
        if all:
            # TODO: make optimization: break cursor iteration after getting already
            # existing user and switch to ids REST method
            user.followers.clear()
            cursor = tweepy.Cursor(user.tweepy._api.followers, id=user.pk, count=count)
            for instance in cursor.items():
                instance = self.parse_response_object(instance)
                instance = self.get_or_create_from_instance(instance)
                user.followers.add(instance)
        else:
            raise NotImplementedError("This method implemented only with argument all=True")
        return user.followers.all()

    def _______get_or_create_from_instance(self, instance):
        try:
            instance_old = self.model.objects.get(screen_name=instance.screen_name)
            if instance_old.pk == instance.pk:
                instance.save()
            else:
                # perhaps we already have old User with the same screen_name, but different id
                try:
                    self.fetch(instance_old.pk)
                except InstagramError, e:
                    if e.code == 34:
                        instance_old.delete()
                        instance.save()
                    else:
                        raise
            return instance
        except self.model.DoesNotExist:
            return super(UserManager, self).get_or_create_from_instance(instance)




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
        '''
        Substitute new user with old one while updating in method Manager.get_or_create_from_instance()
        Can be overrided in child models
        '''
        self.pk = old_instance.pk
        self.created_at = old_instance.created_at

    def save(self, *args, **kwargs):
        '''
        Save all related instances before or after current instance
        '''
        for field, instance in self._foreignkeys_pre_save:
            instance = instance.__class__.remote.get_or_create_from_instance(instance)
            setattr(self, field, instance)
        self._foreignkeys_pre_save = []

        super(InstagramModel, self).save(*args, **kwargs)

    def parse(self):
        '''
        Parse API response and define fields with values
        '''
        for key, value in self._response.items():
            if key == '_api':
                continue

            try:
                field, model, direct, m2m = self._meta.get_field_by_name(key)
            except FieldDoesNotExist:
                log.debug('Field with name "%s" doesn\'t exist in the model %s' % (key, type(self)))
                continue

            if isinstance(field, RelatedObject) and value:
                for item in value:
                    rel_instance = field.model.remote.parse_response_object(item)
                    self._external_links_post_save += [(field.field.name, rel_instance)]
            else:
                if isinstance(field, (models.BooleanField)):
                    value = bool(value)

                elif isinstance(field, (models.OneToOneField, models.ForeignKey)) and value:
                    rel_instance = field.rel.to.remote.parse_response_object(value)
                    value = rel_instance
                    if isinstance(field, models.ForeignKey):
                        self._foreignkeys_pre_save += [(key, rel_instance)]

                elif isinstance(field, (fields.CommaSeparatedCharField, models.CommaSeparatedIntegerField)) and isinstance(value, list):
                    value = ','.join([unicode(v) for v in value])

                elif isinstance(field, (models.CharField, models.TextField)) and value:
                    if isinstance(value, (str, unicode)):
                        value = value.strip()

                setattr(self, key, value)



class InstagramBaseModel(InstagramModel):

    _tweepy_model = None
    _response = None

    created_at = models.DateTimeField(auto_now_add=True)
    fetched = models.DateTimeField(u'Fetched', null=True, blank=True)
    #lang = models.CharField(max_length=10)
    #entities = fields.JSONField()

    class Meta:
        abstract = True

    def set_tweepy(self, model):
        self._tweepy_model = model
        self._response = dict(self._tweepy_model.__dict__)

    @property
    def tweepy(self):
        if not self._tweepy_model:
            # get fresh instance with the same ID, set tweepy object and refresh attributes
            instance = self.__class__.remote.get(self.pk)
            self.set_tweepy(instance.tweepy)
            self.parse()
        return self._tweepy_model

    def get_url(self):
        return 'https://instagram.com/%s' % self.slug


class User(InstagramBaseModel):

    id = models.BigIntegerField(primary_key=True)
    username = models.CharField(max_length=50, unique=True)
    full_name = models.CharField(max_length=255)
    bio = models.CharField("BIO", max_length=255)

    profile_picture = models.URLField(max_length=300)
    website = models.URLField(max_length=300)

    followers_count = models.PositiveIntegerField(null=True)
    media_count = models.PositiveIntegerField(null=True)

    #followers = ManyToManyHistoryField('User', versions=True)

    objects = models.Manager()
    remote = UserManager(methods={
        'get': 'user',
    })

    def __unicode__(self):
        return self.username

    def parse(self):
        #self._response['favorites_count'] = self._response.pop('favourites_count', None)
        #self._response.pop('status', None)
        super(User, self).parse()

    def fetch_followers(self, **kwargs):
        return User.remote.fetch_followers_for_user(user=self, **kwargs)

    def get_followers_ids(self, **kwargs):
        return User.remote.get_followers_ids_for_user(user=self, **kwargs)

    def fetch_statuses(self, **kwargs):
        return Status.remote.fetch_for_user(user=self, **kwargs)


class MediaManager(InstagramManager):
    pass


class Media(InstagramBaseModel):

    id = models.CharField(max_length=100, primary_key=True)
    caption = models.CharField(max_length=255)
    link = models.URLField(max_length=300)

    #tags =
    created_time = models.DateTimeField()

    comment_count = models.PositiveIntegerField(null=True)
    like_count = models.PositiveIntegerField(null=True)

    user = models.ForeignKey(User, related_name="media_feed")

    remote = MediaManager(methods={
        'get': 'media',
    })

    def fetch_comments(self):
        return Comment.remote.fetch_media_comments(self)


class CommentManager(InstagramManager):
    def fetch_media_comments(self, media):

        extra_fields = {}
        extra_fields['fetched'] = timezone.now()
        extra_fields['media_id'] = media.id

        #comments
        response = self.api.media_comments(media.id)
        result = self.parse_response(response, extra_fields)
        return [self.get_or_create_from_instance(instance) for instance in result]

class Comment(InstagramBaseModel):

    user = models.ForeignKey(User)
    media = models.ForeignKey(Media, related_name="comments")

    id = models.BigIntegerField(primary_key=True)
    text = models.TextField()
    #created_at = models.DateTimeField()

    remote = CommentManager()




