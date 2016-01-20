# -*- coding: utf-8 -*-
from datetime import datetime

import mock
from django.conf import settings
from django.test import TestCase
from django.utils import timezone
from instagram import models
from instagram.bind import InstagramAPIError

from .factories import UserFactory, MediaFactory
from .models import Media, User, Tag
from .api import InstagramError


USER_ID = 237074561  # tnt_online
USER_PRIVATE_ID = 176980649
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

        u = User.remote.get_by_slug('tnt_online')

        self.assertEqual(int(u.id), USER_ID)
        self.assertEqual(u.username, 'tnt_online')
        self.assertEqual(u.full_name, u'Телеканал ТНТ')
        self.assertGreater(len(u.profile_picture), 0)
        self.assertGreater(len(u.website), 0)

    def test_search_users(self):

        users = User.remote.search('tnt_online')
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
        self.assertGreater(u.follows_count, 0)
        self.assertGreater(u.media_count, 0)

        self.assertGreater(u.fetched, self.time)

        u.followers_count = None
        u.save()
        self.assertIsNone(u.followers_count)

        u.refresh()
        self.assertGreater(u.followers_count, 0)

        u = User.objects.get(id=u.id)
        self.assertGreater(u.followers_count, 0)

    def test_fetch_private_user(self):

        with self.assertRaises(InstagramError):
            User.remote.fetch(USER_PRIVATE_ID)

        userf = UserFactory(id=USER_PRIVATE_ID)
        user = User.remote.fetch(USER_PRIVATE_ID)

        self.assertEqual(userf, user)
        self.assertFalse(userf.is_private)
        self.assertTrue(user.is_private)

    def test_fetch_user_followers(self):
        u = User.remote.fetch(USER_ID_3)
        followers = u.fetch_followers()

        self.assertGreaterEqual(u.followers_count, 600)
        self.assertEqual(u.followers_count, followers.count())

        # check counts for follower
        f = followers[0]
        self.assertIsNone(f.followers_count)
        self.assertIsNone(f.follows_count)
        self.assertIsNone(f.media_count)

        f = User.remote.fetch(f.id)
        self.assertIsNotNone(f.followers_count)
        self.assertIsNotNone(f.follows_count)
        self.assertIsNotNone(f.media_count)

        # repeat fetching followers and check counts
        u.fetch_followers()
        f = User.objects.get(id=f.id)
        self.assertIsNotNone(f.followers_count)
        self.assertIsNotNone(f.follows_count)
        self.assertIsNotNone(f.media_count)

    def test_fetch_duplicate_user(self):

        u = UserFactory(username='tnt_online')

        self.assertEqual(User.objects.count(), 1)
        self.assertNotEqual(int(u.id), USER_ID)
        self.assertEqual(u.username, 'tnt_online')

        u = User.remote.fetch(USER_ID)

        self.assertEqual(User.objects.count(), 1)
        self.assertEqual(int(u.id), USER_ID)
        self.assertEqual(u.username, 'tnt_online')

    def test_fetch_duble_duplicate_user(self):

        u1 = UserFactory(username='tnt_online', id=8910216)
        u2 = UserFactory(username='bmwru', id=237074561)

        self.assertEqual(User.objects.count(), 2)
        self.assertEqual(int(u1.id), 8910216)
        self.assertEqual(int(u2.id), 237074561)
        self.assertEqual(u1.username, 'tnt_online')
        self.assertEqual(u2.username, 'bmwru')

        u1 = User.remote.fetch(8910216)
        u2 = User.remote.fetch(237074561)

        self.assertEqual(User.objects.count(), 2)
        self.assertEqual(int(u1.id), 8910216)
        self.assertEqual(int(u2.id), 237074561)
        self.assertEqual(u1.username, 'bmwru')
        self.assertEqual(u2.username, 'tnt_online')

    def test_fetch_real_duplicates_user(self):

        u = User.remote.fetch(2116301016)
        self.assertEqual(u.username, 'elena2048')

        with self.assertRaises(InstagramError):
            User.remote.get(1206219929)

        try:
            User.remote.get(1206219929)
        except InstagramError as e:
            self.assertEqual(e.code, 400)

    def test_fetch_likes_with_real_duplicates_user(self):

        user_dead = UserFactory(id=1525127853, username='ich_liebe_dich_05')
        media = MediaFactory(remote_id='1129836810225933436_2235087902')
        media.fetch_likes()

        self.assertNotEqual(User.objects.get(username=user_dead.username), user_dead.id)
        self.assertTrue('temp' in User.objects.get(id=user_dead.id).username)


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


# class InstagramApiTest(UserTest, MediaTest):
#     def call(api, *a, **kw):
#         raise InstagramAPIError(503, "Rate limited", "Your client is making too many request per second")
#
#     @mock.patch('instagram.client.InstagramAPI.user', side_effect=call)
#     @mock.patch('instagram_api.api.InstagramApi.repeat_call',
#                 side_effect=lambda *a, **kw: models.User.object_from_dictionary({'id': '205828054'}))
#     def test_client_rate_limit(self, call, repeat_call):
#         self.assertGreaterEqual(len(CLIENT_IDS), 2)
#         User.remote.fetch(USER_ID_2)
#         self.assertEqual(call.called, True)
#         self.assertEqual(repeat_call.called, True)
