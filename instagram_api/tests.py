# -*- coding: utf-8 -*-
from datetime import datetime

from django.test import TestCase
from django.conf import settings
from django.utils import timezone
from unittest.case import _sentinel, _AssertRaisesContext

from .factories import UserFactory, LocationFactory
from .models import Media, User, Tag, Location
from .api import InstagramError


USER_ID = 237074561  # tnt_online
USER_PRIVATE_ID = 176980649
USER_ID_2 = 775667951  # about 200 media
USER_ID_3 = 1741896487  # about 400 followers
MEDIA_ID = '934625295371059186_205828054'
MEDIA_ID_2 = '806703315661297054_190931988'  # media without caption
LOCATION_ID = 1
TAG_NAME = "snowyday"
TAG_SEARCH_NAME = "snowy"
LOCATION_SEARCH_NAME = "Dog Patch Labs"

TOKEN = '1687258424.fac34ad.34a30c3152014c41abde0da40740077c'


class InstagramApiTestCase(TestCase):

    _settings = None

    def setUp(self):
        context = getattr(settings, 'SOCIAL_API_CALL_CONTEXT', {})
        self._settings = dict(context)
        context.update({'instagram': {'token': TOKEN}})

    def tearDown(self):
        setattr(settings, 'SOCIAL_API_CALL_CONTEXT', self._settings)


class UserTest(InstagramApiTestCase):

    def setUp(self):
        super(UserTest, self).setUp()
        self.time = timezone.now()

    def test_fetch_user_by_name(self):

        u = User.remote.get_by_slug('tnt_online')

        self.assertEqual(int(u.id), USER_ID)
        self.assertEqual(u.username, 'tnt_online')
        self.assertEqual(u.full_name, u'Телеканал ТНТ')
        self.assertGreater(len(u.profile_picture), 0)
        self.assertGreater(len(u.website), 0)

    def test_fetch_bad_string(self):

        u = User.remote.get_by_slug('beautypageantsfans')
        self.assertEqual(u.full_name,
                         u'I Am A Girl \xbfAnd What?\ud83d\udc81\ud83c\udffb\u2728\ud83d\udc51\ud83d\udc8b')

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

    def test_fetch_user_follows(self):
        u = User.remote.fetch(USER_ID_3)
        users = u.fetch_follows()

        self.assertGreaterEqual(u.follows_count, 970)
        self.assertEqual(u.follows_count, users.count())

    def test_fetch_user_followers(self):
        u = User.remote.fetch(USER_ID_3)
        users = u.fetch_followers()

        self.assertGreaterEqual(u.followers_count, 750)
        self.assertEqual(u.followers_count, users.count())

        # check counts for any first public follower
        for f in users:
            self.assertIsNone(f.followers_count)
            self.assertIsNone(f.follows_count)
            self.assertIsNone(f.media_count)

            f = User.remote.fetch(f.id)
            if f.is_private is False:
                self.assertIsNotNone(f.followers_count)
                self.assertIsNotNone(f.follows_count)
                self.assertIsNotNone(f.media_count)
                break

        # fetch followers once again and check counts
        u.fetch_followers()
        f = User.objects.get(id=f.id)
        self.assertIsNotNone(f.followers_count)
        self.assertIsNotNone(f.follows_count)
        self.assertIsNotNone(f.media_count)

    def test_fetch_users_with_full_name_overlength(self):
        user = User.remote.fetch(47274770)
        self.assertEqual(user.full_name, u'Stas from Ishim Ишим Тюмень Ty')
        user = User.remote.fetch(2057367004)
        self.assertEqual(user.full_name, u'Кератин, Ботокс в Краснодаре ')

    def test_fetch_duplicate_user(self):

        u = UserFactory(id=0, username='tnt_online')

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

        UserFactory(id=2116301016)
        User.remote.fetch(2116301016)

        with self.assertRaisesWithCode(InstagramError, 400):
            User.remote.get(1206219929)

    def test_fetch_private_user(self):

        with self.assertRaisesWithCode(InstagramError, 400):
            User.remote.fetch(USER_PRIVATE_ID)

        userf = UserFactory(id=USER_PRIVATE_ID)
        user = User.remote.fetch(USER_PRIVATE_ID)

        self.assertEqual(userf, user)
        self.assertFalse(userf.is_private)
        self.assertTrue(user.is_private)

        userf.refresh()
        self.assertTrue(userf.is_private)

    def test_unexisted_user(self):
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


class MediaTest(InstagramApiTestCase):

    def setUp(self):
        super(MediaTest, self).setUp()
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
        self.assertEqual(m.filter, 'Normal')

        self.assertGreater(len(m.image_low_resolution), 0)
        self.assertGreater(len(m.image_standard_resolution), 0)
        self.assertGreater(len(m.image_thumbnail), 0)
        self.assertGreater(len(m.video_low_bandwidth), 0)
        self.assertGreater(len(m.video_low_resolution), 0)
        self.assertGreater(len(m.video_standard_resolution), 0)

        self.assertGreater(m.comments.count(), 0)
        self.assertGreater(m.tags.count(), 0)
        # self.assertGreater(m.likes_users.count(), 0)

        # media without caption test
        m = Media.remote.fetch(MEDIA_ID_2)
        self.assertEqual(len(m.caption), 0)

        self.assertEqual(m.type, 'image')

        self.assertGreater(len(m.image_low_resolution), 0)
        self.assertGreater(len(m.image_standard_resolution), 0)
        self.assertGreater(len(m.image_thumbnail), 0)

        self.assertGreater(m.comments.count(), 0)
        # self.assertGreater(m.likes_users.count(), 0)

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
        media = u.fetch_media()

        self.assertGreater(media.count(), 210)
        self.assertEqual(media.count(), u.media_count)
        self.assertEqual(media.count(), u.media_feed.count())

        after = media.order_by('-created_time')[50].created_time
        Media.objects.all().delete()

        self.assertEqual(u.media_feed.count(), 0)

        media = u.fetch_media(after=after)

        self.assertEqual(media.count(), 53)  # not 50 for some strange reason
        self.assertEqual(media.count(), u.media_feed.count())

    def test_fetch_media_with_location(self):

        media = Media.remote.fetch('1105137931436928268_1692711770')

        self.assertIsInstance(media.location, Location)
        self.assertEqual(media.location.name, 'Prague, Czech Republic')

    def test_fetch_comments(self):
        m = Media.remote.fetch(MEDIA_ID)
        comments = m.fetch_comments()

        self.assertGreater(m.comments_count, 0)
        # TODO: 84 != 80 strange bug of API, may be limit of comments to fetch
        # self.assertEqual(m.comments_count, len(comments))

        c = comments[0]
        self.assertEqual(c.media, m)
        self.assertGreater(len(c.text), 0)
        self.assertGreater(c.fetched, self.time)
        self.assertIsInstance(c.created_time, datetime)

    def test_fetch_likes(self):
        m = Media.remote.fetch(MEDIA_ID)
        likes = m.fetch_likes()

        self.assertGreater(m.likes_count, 0)
        # TODO: 2515 != 117 how to get all likes?
        # self.assertEqual(m.likes_count, likes.count())
        self.assertIsInstance(likes[0], User)


class TagTest(InstagramApiTestCase):
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
        media = t.fetch_media()

        self.assertGreater(media.count(), 0)
        self.assertEqual(media.count(), t.media_feed.count())


class LocationTest(InstagramApiTestCase):
    def test_fetch_location(self):
        location = Location.remote.fetch(LOCATION_ID)

        self.assertEqual(location.id, LOCATION_ID)
        self.assertEqual(location.name, "Dog Patch Labs")
        self.assertEqual(location.latitude, 37.782492553)
        self.assertEqual(location.longitude, -122.387785235)
        self.assertEqual(location.media_count, None)

    def test_search_locations(self):
        locations = Location.remote.search(lat=37.782492553, lng=-122.387785235)

        self.assertGreater(len(locations), 0)
        for location in locations:
            self.assertIsInstance(location, Location)

    def test_fetch_location_media(self):
        location = LocationFactory(id=LOCATION_ID)
        media = location.fetch_media()

        self.assertGreater(media.count(), 0)
        self.assertEqual(media.count(), location.media_feed.count())
        self.assertEqual(media.count(), location.media_count)


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
