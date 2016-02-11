# -*- coding: utf-8 -*-
from datetime import datetime

from django.test import TestCase
from django.utils import timezone
from social_api.api import override_api_context
from unittest.case import _sentinel, _AssertRaisesContext

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

TOKEN = '1687258424.fac34ad.34a30c3152014c41abde0da40740077c'


class UserTest(TestCase):

    def setUp(self):
        self.time = timezone.now()

    def test_fetch_user_by_name(self):

        with override_api_context('instagram', token=TOKEN):
            u = User.remote.get_by_slug('tnt_online')

        self.assertEqual(int(u.id), USER_ID)
        self.assertEqual(u.username, 'tnt_online')
        self.assertEqual(u.full_name, u'Телеканал ТНТ')
        self.assertGreater(len(u.profile_picture), 0)
        self.assertGreater(len(u.website), 0)

    def test_search_users(self):

        with override_api_context('instagram', token=TOKEN):
            users = User.remote.search('tnt_online')

        self.assertGreater(len(users), 0)
        for user in users:
            self.assertIsInstance(user, User)

    def test_fetch_user(self):
        with override_api_context('instagram', token=TOKEN):
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

        with override_api_context('instagram', token=TOKEN):
            u.refresh()
        self.assertGreater(u.followers_count, 0)

        u = User.objects.get(id=u.id)
        self.assertGreater(u.followers_count, 0)

    def test_fetch_user_followers(self):
        with override_api_context('instagram', token=TOKEN):
            u = User.remote.fetch(USER_ID_3)
            followers = u.fetch_followers()

        self.assertGreaterEqual(u.followers_count, 600)
        self.assertEqual(u.followers_count, followers.count())

        # check counts for follower
        f = followers[1]
        self.assertIsNone(f.followers_count)
        self.assertIsNone(f.follows_count)
        self.assertIsNone(f.media_count)

        with override_api_context('instagram', token=TOKEN):
            f = User.remote.fetch(f.id)
        self.assertIsNotNone(f.followers_count)
        self.assertIsNotNone(f.follows_count)
        self.assertIsNotNone(f.media_count)

        with override_api_context('instagram', token=TOKEN):
            # repeat fetching followers and check counts
            u.fetch_followers()
        f = User.objects.get(id=f.id)
        self.assertIsNotNone(f.followers_count)
        self.assertIsNotNone(f.follows_count)
        self.assertIsNotNone(f.media_count)

    def test_fetch_duplicate_user(self):

        with override_api_context('instagram', token=TOKEN):
            u = UserFactory(username='tnt_online')

        self.assertEqual(User.objects.count(), 1)
        self.assertNotEqual(int(u.id), USER_ID)
        self.assertEqual(u.username, 'tnt_online')

        with override_api_context('instagram', token=TOKEN):
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

        with override_api_context('instagram', token=TOKEN):
            u1 = User.remote.fetch(8910216)
            u2 = User.remote.fetch(237074561)

        self.assertEqual(User.objects.count(), 2)
        self.assertEqual(int(u1.id), 8910216)
        self.assertEqual(int(u2.id), 237074561)
        self.assertEqual(u1.username, 'bmwru')
        self.assertEqual(u2.username, 'tnt_online')

    def test_fetch_real_duplicates_user(self):

        with override_api_context('instagram', token=TOKEN):
            UserFactory(id=2116301016)
            User.remote.fetch(2116301016)

            with self.assertRaisesWithCode(InstagramError, 400):
                User.remote.get(1206219929)

    def test_fetch_private_user(self):

        with override_api_context('instagram', token=TOKEN):
            with self.assertRaisesWithCode(InstagramError, 400):
                User.remote.fetch(USER_PRIVATE_ID)

            userf = UserFactory(id=USER_PRIVATE_ID)
            user = User.remote.fetch(USER_PRIVATE_ID)

        self.assertEqual(userf, user)
        self.assertFalse(userf.is_private)
        self.assertTrue(user.is_private)

    def test_unexisted_user(self):
        with override_api_context('instagram', token=TOKEN):
            with self.assertRaisesWithCode(InstagramError, 400):
                User.remote.get(0)

    def assertRaisesWithCode(self, excClass, code, callableObj=_sentinel, *args, **kwargs):
        context = _AssertRaisesContext(excClass, self)
        if callableObj is _sentinel:
            return context
        with context:
            callableObj(*args, **kwargs)

        try:
            callableObj(*args, **kwargs)
        except excClass as e:
            self.assertEqual(e.code, code)


class MediaTest(TestCase):

    def setUp(self):
        self.time = timezone.now()

    def test_fetch_media(self):
        with override_api_context('instagram', token=TOKEN):
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
        with override_api_context('instagram', token=TOKEN):
            m = Media.remote.fetch(MEDIA_ID_2)
        self.assertEqual(len(m.caption), 0)

        self.assertEqual(m.type, 'image')

        self.assertGreater(len(m.image_low_resolution), 0)
        self.assertGreater(len(m.image_standard_resolution), 0)
        self.assertGreater(len(m.image_thumbnail), 0)

    def test_fetch_user_media_count(self):
        u = UserFactory(id=USER_ID)

        with override_api_context('instagram', token=TOKEN):
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
        with override_api_context('instagram', token=TOKEN):
            u = User.remote.fetch(USER_ID_2)
            medias = u.fetch_media()

        self.assertGreater(medias.count(), 210)
        self.assertEqual(medias.count(), u.media_count)
        self.assertEqual(medias.count(), u.media_feed.count())

        after = medias.order_by('-created_time')[50].created_time
        Media.objects.all().delete()

        self.assertEqual(u.media_feed.count(), 0)

        with override_api_context('instagram', token=TOKEN):
            medias = u.fetch_media(after=after)

        self.assertEqual(medias.count(), 52)  # not 50 for some reason
        self.assertEqual(medias.count(), u.media_feed.count())

    def test_fetch_comments(self):
        with override_api_context('instagram', token=TOKEN):
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
        with override_api_context('instagram', token=TOKEN):
            m = Media.remote.fetch(MEDIA_ID)
            likes = m.fetch_likes()

        self.assertGreater(m.likes_count, 0)
        self.assertEqual(m.likes_count, likes.count())  # TODO: get all likes


class TagTest(TestCase):
    def setUp(self):
        pass

    def test_fetch_tag(self):
        with override_api_context('instagram', token=TOKEN):
            t = Tag.remote.fetch(TAG_NAME)

        self.assertEqual(t.name, TAG_NAME)
        self.assertGreater(t.media_count, 0)

    def test_search_tags(self):

        with override_api_context('instagram', token=TOKEN):
            tags = Tag.remote.search(TAG_SEARCH_NAME)

        self.assertGreater(len(tags), 0)
        for tag in tags:
            self.assertIsInstance(tag, Tag)

    def test_fetch_tag_media(self):
        with override_api_context('instagram', token=TOKEN):
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
