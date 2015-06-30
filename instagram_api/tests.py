# -*- coding: utf-8 -*-
from datetime import datetime

import mock
from django.conf import settings
from django.test import TestCase
from django.utils import timezone
from instagram import models
from instagram.bind import InstagramAPIError

from .factories import UserFactory
from .models import Media, User, Tag
from .api import CLIENT_IDS


USER_ID = 237074561  # tnt_online
USER_NAME = 'tnt_online'
USER_ID_2 = 775667951  # about 200 media
USER_ID_3 = 1741896487  # about 400 followers
MEDIA_ID = '934625295371059186_205828054'
MEDIA_ID_2 = '806703315661297054_190931988'  # media without caption
TAG_NAME = "snowyday"
TAG_SEARCH_NAME = "snowy"


class UserTest(TestCase):
    def setUp(self):
        self.time = timezone.now()

    def test_fetch_user_by_name(self):

        u = User.remote.get_by_slug(USER_NAME)

        self.assertEqual(int(u.id), USER_ID)
        self.assertEqual(u.username, 'tnt_online')
        self.assertEqual(u.full_name, u'Телеканал ТНТ')
        self.assertGreater(len(u.profile_picture), 0)
        self.assertGreater(len(u.website), 0)

    def test_search_users(self):

        users = User.remote.search(USER_NAME)
        self.assertGreater(len(users), 0)
        for user in users:
            self.assertIsInstance(user, User)

    def test_fetch_user(self):
        u = User.remote.fetch(USER_ID)

        self.assertEqual(int(u.id), USER_ID)
        self.assertEqual(u.username, 'tnt_online')
        self.assertEqual(u.full_name, u'Телеканал ТНТ')
        self.assertGreater(len(u.profile_picture), 0)
        self.assertGreater(len(u.website), 0)

        self.assertGreater(u.followers_count, 0)
        self.assertGreater(u.media_count, 0)

        self.assertGreater(u.fetched, self.time)

    def test_fetch_user_followers(self):
        u = User.remote.fetch(USER_ID_3)
        followers = u.fetch_followers()

        self.assertGreaterEqual(u.followers_count, 600)
        self.assertEqual(u.followers_count, followers.count())  # TODO: strange bug of API


class MediaTest(TestCase):
    def setUp(self):
        self.time = timezone.now()

    def test_fetch_media(self):
        m = Media.remote.fetch(MEDIA_ID)

        self.assertEqual(m.remote_id, MEDIA_ID)
        self.assertGreater(len(m.caption), 0)
        self.assertGreater(len(m.link), 0)

        self.assertGreater(m.comments_count, 0)
        self.assertGreater(m.likes_count, 0)

        self.assertGreater(m.fetched, self.time)
        self.assertIsInstance(m.created_time, datetime)

        self.assertEqual(m.type, 'video')

        self.assertGreater(len(m.image_low_resolution), 0)
        self.assertGreater(len(m.image_standard_resolution), 0)
        self.assertGreater(len(m.image_thumbnail), 0)

        self.assertGreater(len(m.video_low_bandwidth), 0)
        self.assertGreater(len(m.video_low_resolution), 0)
        self.assertGreater(len(m.video_standard_resolution), 0)

        # media without caption test
        m = Media.remote.fetch(MEDIA_ID_2)
        self.assertEqual(len(m.caption), 0)

        self.assertEqual(m.type, 'image')

        self.assertGreater(len(m.image_low_resolution), 0)
        self.assertGreater(len(m.image_standard_resolution), 0)
        self.assertGreater(len(m.image_thumbnail), 0)

    def test_fetch_user_media_count(self):
        u = UserFactory(id=USER_ID)

        media = u.fetch_media(count=100)
        m = media[0]

        self.assertEqual(media.count(), 100)
        self.assertEqual(m.user, u)

        self.assertGreater(len(m.caption), 0)
        self.assertGreater(len(m.link), 0)

        self.assertGreater(m.comments_count, 0)
        self.assertGreater(m.likes_count, 0)

        self.assertGreater(m.fetched, self.time)
        self.assertIsInstance(m.created_time, datetime)

    def test_fetch_user_media(self):
        u = User.remote.fetch(USER_ID_2)
        medias = u.fetch_media()

        self.assertGreater(medias.count(), 210)
        self.assertEqual(medias.count(), u.media_count)
        self.assertEqual(medias.count(), u.media_feed.count())

        after = medias.order_by('-created_time')[50].created_time
        Media.objects.all().delete()

        self.assertEqual(u.media_feed.count(), 0)

        medias = u.fetch_media(after=after)

        self.assertEqual(medias.count(), 52)  # not 50 for some reason
        self.assertEqual(medias.count(), u.media_feed.count())

    def test_fetch_comments(self):
        m = Media.remote.fetch(MEDIA_ID)

        comments = m.fetch_comments()

        self.assertGreater(m.comments_count, 0)
        self.assertEqual(m.comments_count, len(comments))  # TODO: strange bug of API

        c = comments[0]
        self.assertEqual(c.media, m)

        self.assertGreater(len(c.text), 0)

        self.assertGreater(c.fetched, self.time)
        self.assertIsInstance(c.created_at, datetime)

    def test_fetch_likes(self):
        m = Media.remote.fetch(MEDIA_ID)

        likes = m.fetch_likes()

        self.assertGreater(m.likes_count, 0)
        self.assertEqual(m.likes_count, likes.count())  # TODO: get all likes


class TagTest(TestCase):
    def setUp(self):
        pass

    def test_fetch_tag(self):
        t = Tag.remote.fetch(TAG_NAME)

        self.assertEqual(t.name, TAG_NAME)
        self.assertGreater(t.media_count, 0)

    def test_search_tags(self):

        tags = Tag.remote.search(TAG_SEARCH_NAME)
        self.assertGreater(len(tags), 0)
        for tag in tags:
            self.assertIsInstance(tag, Tag)

    def test_fetch_tag_media(self):
        t = Tag.remote.fetch("merrittislandnwr")
        medias = t.fetch_media()

        self.assertGreater(medias.count(), 0)

        self.assertEqual(medias.count(), t.media_feed.count())


class InstagramApiTest(UserTest, MediaTest):
    def call(api, *a, **kw):
        raise InstagramAPIError(503, "Rate limited", "Your client is making too many request per second")

    @mock.patch('instagram.client.InstagramAPI.user', side_effect=call)
    @mock.patch('instagram_api.api.InstagramApi.repeat_call',
                side_effect=lambda *a, **kw: models.User.object_from_dictionary({'id': '205828054'}))
    def test_client_rate_limit(self, call, repeat_call):
        self.assertGreaterEqual(len(CLIENT_IDS), 2)
        User.remote.fetch(USER_ID_2)
        self.assertEqual(call.called, True)
        self.assertEqual(repeat_call.called, True)
