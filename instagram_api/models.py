# -*- coding: utf-8 -*-
from datetime import datetime
import logging
import re
import time
import sys
import six

from django.db import models
from django.db.models.fields import FieldDoesNotExist
from django.db.utils import IntegrityError
from django.utils import timezone
from instagram.helper import timestamp_to_datetime
from instagram.models import ApiModel
from m2m_history.fields import ManyToManyHistoryField
from social_api.utils import override_api_context

from . import fields
from .api import api_call, InstagramError
from .decorators import atomic

try:
    from django.db.models.related import RelatedObject as ForeignObjectRel
except ImportError:
    # django 1.8 +
    from django.db.models.fields.related import ForeignObjectRel

__all__ = ['User', 'Media', 'Comment', 'InstagramContentError', 'InstagramModel', 'InstagramManager', 'UserManager'
           'Tag', 'TagManager']

log = logging.getLogger('instagram_api')


class InstagramContentError(Exception):
    pass


class InstagramManager(models.Manager):
    """
    Instagram Manager for RESTful CRUD operations
    """
    def __init__(self, methods=None, remote_pk=None, *args, **kwargs):
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
        return api_call(method, *args, **kwargs)

    def fetch(self, *args, **kwargs):
        """
        Retrieve and save object to local DB
        """
        result = self.get(*args, **kwargs)
        if isinstance(result, list):
            instances = self.model.objects.none()
            for instance in result:
                instance = self.get_or_create_from_instance(instance)
                instances |= instance.__class__.objects.filter(pk=instance.pk)
            return instances
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
            raise InstagramContentError('Instagram response should be list or ApiModel, not %s' % response)

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

    class Meta:
        abstract = True

    def save(self, *args, **kwargs):
        # cut all CharFields to max allowed length
        cut = False
        for field in self._meta.fields:
            if isinstance(field, (models.CharField, models.TextField)):
                value = getattr(self, field.name)
                if isinstance(field, models.CharField) and value:
                    if len(value) > field.max_length:
                        value = value[:field.max_length]
                        cut = True
                if isinstance(value, six.string_types):
                    # check strings for bad symbols in string encoding
                    # there is problems to save users with bad encoded strings
                    while True:
                        try:
                            value.encode('utf-16').decode('utf-16')
                            break
                        except UnicodeDecodeError:
                            if cut and len(value) > 2:
                                value = value[:-1]
                            else:
                                value = ''
                                break
                setattr(self, field.name, value)

        try:
            super(InstagramModel, self).save(*args, **kwargs)
        except Exception as e:
            six.reraise(type(e), '%s while saving %s' % (str(e), self.__dict__), sys.exc_info()[2])


class InstagramBaseModel(InstagramModel):
    _refresh_pk = 'id'

    fetched = models.DateTimeField(u'Fetched', null=True, blank=True)
    objects = models.Manager()

    class Meta:
        abstract = True

    def __init__(self, *args, **kwargs):
        super(InstagramBaseModel, self).__init__(*args, **kwargs)

        # different lists for saving related objects
        self._relations_post_save = {'fk': {}, 'm2m': {}}
        self._relations_pre_save = []
        self._tweepy_model = None
        self._response = {}

    def _substitute(self, old_instance):
        """
        Substitute new user with old one while updating in method Manager.get_or_create_from_instance()
        Can be overrided in child models
        """
        self.pk = old_instance.pk

    def save(self, *args, **kwargs):
        """
        Save all related instances before or after current instance
        """
        for field, instance in self._relations_pre_save:
            instance = instance.__class__.remote.get_or_create_from_instance(instance)
            setattr(self, field, instance)
        self._relations_pre_save = []

        try:
            super(InstagramBaseModel, self).save(*args, **kwargs)
        except Exception as e:
            six.reraise(type(e), '%s while saving %s' % (str(e), self.__dict__), sys.exc_info()[2])

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

            if isinstance(field, ForeignObjectRel) and value:
                self._relations_post_save['fk'][key] = [field.model.remote.parse_response_object(item)
                                                        for item in value]
            elif isinstance(field, models.ManyToManyField) and value:
                self._relations_post_save['m2m'][key] = [field.rel.to.remote.parse_response_object(item)
                                                         for item in value]
            else:
                if isinstance(field, models.BooleanField):
                    value = bool(value)

                elif isinstance(field, (models.OneToOneField, models.ForeignKey)) and value:
                    rel_instance = field.rel.to.remote.parse_response_object(value)
                    value = rel_instance
                    if isinstance(field, models.ForeignKey):
                        self._relations_pre_save += [(key, rel_instance)]

                elif isinstance(field, (fields.CommaSeparatedCharField,
                                        models.CommaSeparatedIntegerField)) and isinstance(value, list):
                    value = ','.join([unicode(v) for v in value])

                elif isinstance(field, (models.CharField, models.TextField)) and value:
                    if isinstance(value, (str, unicode)):
                        value = value.strip()

                elif isinstance(field, models.IntegerField) and value:
                    value = int(value)

                setattr(self, key, value)

    def get_url(self):
        return 'https://instagram.com/%s' % self.slug

    def refresh(self):
        """
        Refresh current model with remote data
        """
        instance = self.__class__.remote.fetch(getattr(self, self._refresh_pk))
        self.__dict__.update(instance.__dict__)


class InstagramSearchManager(InstagramManager):
    def search(self, q=None, **kwargs):
        if q:
            kwargs['q'] = q
        instances = self.api_call('search', **kwargs)

        if isinstance(instances[0], list) and (len(instances) > 1) and \
                (isinstance(instances[1], basestring) or instances[1] is None):
            instances, _next = instances
            while _next:
                instances_new, _next = self.api_call('search', with_next_url=_next)
                [instances.append(i) for i in instances_new]

        extra_fields = kwargs.pop('extra_fields', {})
        extra_fields['fetched'] = timezone.now()

        return self.parse_response_list(instances, extra_fields)


class UserManager(InstagramSearchManager):

    def get(self, *args, **kwargs):
        if 'extra_fields' not in kwargs:
            kwargs['extra_fields'] = {}
        kwargs['extra_fields']['is_private'] = False
        try:
            return super(UserManager, self).get(*args, **kwargs)
        except InstagramError, e:
            if e.code == 400:
                if e.error_type == 'APINotAllowedError':
                    # {'error_message': 'you cannot view this resource',
                    #  'error_type': 'APINotAllowedError',
                    #  'status_code': 400}
                    try:
                        instance = self.model.objects.get(pk=args[0])
                        instance.is_private = True
                        instance.save()
                        return instance
                    except self.model.DoesNotExist:
                        raise e
                elif e.error_type == 'APINotFoundError':
                    # {'error_message': 'this user does not exist',
                    #  'error_type': 'APINotFoundError',
                    #  'status_code': 400}
                    try:
                        instance = self.model.objects.get(pk=args[0])
                        instance.delete()
                        raise
                    except self.model.DoesNotExist:
                        raise e
            else:
                raise

    def fetch_by_slug(self, *args, **kwargs):
        result = self.get_by_slug(*args, **kwargs)
        return self.get_or_create_from_instance(result)

    def get_by_url(self, url):
        """
        Return object by url
        :param url:
        """
        m = re.findall(r'(?:https?://)?(?:www\.)?instagram\.com/([^/]+)/?', url)
        if not len(m):
            raise ValueError("Url should be started with https://instagram.com/")

        return self.get_by_slug(m[0])

    def get_by_slug(self, slug):
        """
        Return existed User by slug or new intance with empty pk
        :param slug:
        """
        users = self.search(slug)
        for user in users:
            if user.username == slug:
                return self.get(user.id)
        raise ValueError("No users found for the name %s" % slug)

    def fetch_followers(self, user):
        return self.create_related_users('followers', user)

    def fetch_follows(self, user):
        return self.create_related_users('follows', user)

    def create_related_users(self, method, user):
        ids = []
        extra_fiels = {'fetched': timezone.now()}

        _next = True
        while _next:
            kwargs = {} if _next is True else {'with_next_url': _next}
            instances, _next = self.api_call(method, user.pk, **kwargs)
            for instance in instances:
                instance = self.parse_response_object(instance, extra_fiels)
                try:
                    with atomic():
                        self.get_or_create_from_instance(instance)
                except IntegrityError:
                    pass
                ids += [instance.id]

        m2m_relation = getattr(user, method)
        initial = m2m_relation.versions.count() == 0
        setattr(user, method, ids) # user.followers = ids

        if initial:
            m2m_relation.get_queryset_through().update(time_from=None)
            m2m_relation.versions.update(added_count=0)

        return m2m_relation.all()

    def fetch_media_likes(self, media):
        # TODO: get all likes
        # https://instagram.com/developer/endpoints/likes/#get_media_likes
        # no pagination to get all likes
        # http://stackoverflow.com/questions/20478485/get-a-list-of-users-who-have-liked-a-media-not-working-anymore

        extra_fields = {'fetched': timezone.now()}

        # users
        response = self.api_call('likes', media.remote_id)
        result = self.parse_response(response, extra_fields)

        instances = []
        for instance in result:
            instance = self.get_or_create_from_instance(instance)
            instances.append(instance)

        media.likes_users = instances + list(media.likes_users.all())

        return media.likes_users.all()


class User(InstagramBaseModel):

    _followers_ids = []
    _follows_ids = []

    id = models.BigIntegerField(primary_key=True)
    username = models.CharField(max_length=30, unique=True)
    full_name = models.CharField(max_length=30)
    bio = models.CharField(max_length=150)

    profile_picture = models.URLField(max_length=112)
    website = models.URLField(max_length=150)  # found max_length=106

    followers_count = models.PositiveIntegerField(null=True, db_index=True)
    follows_count = models.PositiveIntegerField(null=True, db_index=True)
    media_count = models.PositiveIntegerField(null=True, db_index=True)

    followers = ManyToManyHistoryField('User', versions=True, related_name='follows')

    is_private = models.NullBooleanField('Account is private', db_index=True)

    objects = models.Manager()
    remote = UserManager(methods={
        'get': 'user',
        'search': 'user_search',
        'follows': 'user_follows',
        'followers': 'user_followed_by',
        'likes': 'media_likes',
    })

    @property
    def slug(self):
        return self.username

    def __unicode__(self):
        return self.full_name or self.username

    @property
    def instagram_link(self):
        return u'https://instagram.com/%s/' % self.username

    def _substitute(self, old_instance):
        super(User, self)._substitute(old_instance)
        for field_name in ['followers_count', 'follows_count', 'media_count', 'is_private']:
            if getattr(self, field_name) is None and getattr(old_instance, field_name) is not None:
                setattr(self, field_name, getattr(old_instance, field_name))

    def save(self, *args, **kwargs):

        try:
            with atomic():
                super(InstagramBaseModel, self).save(*args, **kwargs)
        except IntegrityError as e:
            if 'username' in e.message:
                # duplicate key value violates unique constraint "instagram_api_user_username_key"
                # DETAIL: Key (username)=(...) already exists.
                user_local = User.objects.get(username=self.username)
                try:
                    # check for recursive loop
                    # get remote user
                    user_remote = User.remote.get(user_local.pk)
                    try:
                        user_local2 = User.objects.get(username=user_remote.username)
                        # if users excahnge usernames or user is dead (400 error)
                        if user_local2.pk == self.pk or user_remote.is_private:
                            user_local.username = 'temp%s' % time.time()
                            user_local.save()
                    except User.DoesNotExist:
                        pass
                    # fetch right user
                    User.remote.fetch(user_local.pk)
                except InstagramError as e:
                    if e.code == 400:
                        user_local.delete()
                    else:
                        raise
                super(InstagramBaseModel, self).save(*args, **kwargs)
            else:
                raise

    def parse(self):
        if isinstance(self._response, dict) and 'counts' in self._response:
            count = self._response['counts']
            self._response['followers_count'] = count.get('followed_by', 0)
            self._response['follows_count'] = count.get('follows', 0)
            self._response['media_count'] = count.get('media', 0)

        super(User, self).parse()

    def fetch_follows(self):
        return User.remote.fetch_follows(user=self)

    def fetch_followers(self):
        return User.remote.fetch_followers(user=self)

    def fetch_media(self, **kwargs):
        return Media.remote.fetch_user_media(user=self, **kwargs)

    def refresh(self):
        # do refresh via client_id, because is_private is dependent on access_token and relation with current user
        with override_api_context('instagram', use_client_id=True):
            super(User, self).refresh()


class MediaManager(InstagramManager):

    def fetch_user_media(self, user, count=None, min_id=None, max_id=None,
                         after=None, before=None):

        extra_fields = {'fetched': timezone.now(), 'user_id': user.pk}
        kwargs = {'user_id': user.pk}

        if count:
            kwargs['count'] = count
        if min_id:
            kwargs['min_id'] = min_id
        if max_id:
            kwargs['max_id'] = max_id
        if after:
            kwargs['min_timestamp'] = time.mktime(after.timetuple())
        if before:
            kwargs['max_timestamp'] = time.mktime(before.timetuple())

        instances, _next = self.api_call('user_recent_media', **kwargs)
        while _next:
            instances_new, _next = self.api_call('user_recent_media', with_next_url=_next)
            instances_new = sorted(instances_new, reverse=True, key=lambda j: j.created_time)
            for i in instances_new:
                instances.append(i)
                # strange, but API arguments doesn't work
                if count and len(instances) >= count or after and i.created_time.replace(tzinfo=timezone.utc) <= after:
                    _next = False
                    break

        for instance in instances:
            instance = self.parse_response_object(instance, extra_fields)
            self.get_or_create_from_instance(instance)

        return user.media_feed.all()

    def fetch_tag_media(self, tag, count=None, max_tag_id=None):

        extra_fields = {'fetched': timezone.now()}

        kwargs = {'tag_name': tag.name, 'count': count, 'max_tag_id': max_tag_id}
        instances, _next = self.api_call('tag_recent_media', **kwargs)
        while _next:
            instances_new, _next = self.api_call('tag_recent_media', with_next_url=_next, tag_name=tag.name)
            [instances.append(i) for i in instances_new]

        for instance in instances:
            extra_fields['user_id'] = instance.user.id
            instance = self.parse_response_object(instance, extra_fields)
            instance = self.get_or_create_from_instance(instance)
            instance.tags.add(tag)

        return tag.media_feed.all()

    def fetch_location_media(self, location, count=None, max_id=None):

        extra_fields = {'fetched': timezone.now()}

        kwargs = {'location_id': location.pk, 'count': count, 'max_id': max_id}
        instances, _next = self.api_call('location_recent_media', **kwargs)
        while _next:
            instances_new, _next = self.api_call('location_recent_media', with_next_url=_next, location_id=location.pk)
            [instances.append(i) for i in instances_new]

        for instance in instances:
            extra_fields['user_id'] = instance.user.id
            extra_fields['location_id'] = location.pk
            instance = self.parse_response_object(instance, extra_fields)
            self.get_or_create_from_instance(instance)

        if count is None:
            location.media_count = location.media_feed.count()
            location.save()

        return location.media_feed.all()


class Media(InstagramBaseModel):
    remote_id = models.CharField(max_length=30, unique=True)
    caption = models.TextField(blank=True)
    link = models.URLField(max_length=68)

    type = models.CharField(max_length=5)
    filter = models.CharField(max_length=40)  # TODO: tune max_length of this field

    image_low_resolution = models.URLField(max_length=200)
    image_standard_resolution = models.URLField(max_length=200)
    image_thumbnail = models.URLField(max_length=200)

    video_low_bandwidth = models.URLField(max_length=130)
    video_low_resolution = models.URLField(max_length=130)
    video_standard_resolution = models.URLField(max_length=130)

    created_time = models.DateTimeField()

    comments_count = models.PositiveIntegerField(null=True)
    likes_count = models.PositiveIntegerField(null=True)

    user = models.ForeignKey('User', related_name="media_feed")
    location = models.ForeignKey('Location', null=True, related_name="media_feed")
    likes_users = ManyToManyHistoryField('User', related_name="likes_media")
    tags = models.ManyToManyField('Tag', related_name='media_feed')

    remote = MediaManager(remote_pk=('remote_id',), methods={
        'get': 'media',
        'user_recent_media': 'user_recent_media',
        'tag_recent_media': 'tag_recent_media',
        'location_recent_media': 'location_recent_media',
    })

    def get_url(self):
        return self.link

    def __unicode__(self):
        return self.caption

    def parse(self):
        self._response['remote_id'] = self._response.pop('id')

        for prefix in ['video', 'image']:
            key = '%ss' % prefix
            if key in self._response:
                for k, v in self._response[key].items():
                    media = self._response[key][k]
                    if isinstance(media, ApiModel):
                        media = media.__dict__
                    self._response['%s_%s' % (prefix, k)] = media['url']

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

        # if 'likes' in self._response:
        #     self._response['likes_users'] = self._response.pop('likes')

        super(Media, self).parse()

    def fetch_comments(self):
        return Comment.remote.fetch_media_comments(self)

    def fetch_likes(self):
        return User.remote.fetch_media_likes(self)

    def save(self, *args, **kwargs):
        if self.caption is None:
            self.caption = ''

        super(Media, self).save(*args, **kwargs)

        for field, relations in self._relations_post_save['fk'].items():
            extra_fields = {'media_id': self.pk, 'owner_id': self.user_id} if field == 'comments' else {}
            for instance in relations:
                instance.__dict__.update(extra_fields)
                instance.__class__.remote.get_or_create_from_instance(instance)

        for field, relations in self._relations_post_save['m2m'].items():
            for instance in relations:
                instance = instance.__class__.remote.get_or_create_from_instance(instance)
                getattr(self, field).add(instance)


class CommentManager(InstagramManager):
    def fetch_media_comments(self, media):
        response = self.api_call('comments', media.remote_id)

        extra_fields = {'fetched': timezone.now(), 'media_id': media.pk, 'owner_id': media.user_id}
        result = self.parse_response(response, extra_fields)

        instances = self.model.objects.none()
        for instance in result:
            instance = self.get_or_create_from_instance(instance)
            instances |= instance.__class__.objects.filter(pk=instance.pk)

        return instances


class Comment(InstagramBaseModel):
    owner = models.ForeignKey(User, related_name='media_comments')
    user = models.ForeignKey(User, related_name='comments')
    media = models.ForeignKey(Media, related_name="comments")

    id = models.BigIntegerField(primary_key=True)
    text = models.TextField()
    created_time = models.DateTimeField()

    remote = CommentManager(methods={
        'comments': 'media_comments',
    })

    def get_url(self):
        return self.media.link

    def parse(self):
        self._response['created_time'] = self._response.pop('created_at')
        super(Comment, self).parse()


class TagManager(InstagramSearchManager):
    pass


class Tag(InstagramBaseModel):
    _refresh_pk = 'name'
    name = models.CharField(max_length=50, unique=True)
    media_count = models.PositiveIntegerField(null=True)

    remote = TagManager(remote_pk=('name',), methods={
        'get': 'tag',
        'search': 'tag_search'
    })

    def __unicode__(self):
        return '#%s' % self.name

    def fetch_media(self, **kwargs):
        return Media.remote.fetch_tag_media(tag=self, **kwargs)


class LocationManager(InstagramSearchManager):
    pass


class Location(InstagramBaseModel):
    id = models.BigIntegerField(primary_key=True)
    name = models.CharField(max_length=100)
    latitude = models.FloatField(null=True)
    longitude = models.FloatField(null=True)
    media_count = models.PositiveIntegerField(null=True)

    remote = LocationManager(methods={
        'get': 'location',
        'search': 'location_search'
    })

    def __unicode__(self):
        return self.name

    def fetch_media(self, **kwargs):
        return Media.remote.fetch_location_media(location=self, **kwargs)

    def parse(self):
        super(Location, self).parse()
        self.latitude = self._response['point'].latitude
        self.longitude = self._response['point'].longitude
