# -*- coding: utf-8 -*-
from datetime import datetime

from django.test import TestCase
from django.utils import timezone

from .models import User, Media
from .factories import UserFactory

USER_ID = 237074561  # tnt_online
USER_NAME = 'tnt_online'
USER_ID_2 = 775667951  # about 200 media
USER_ID_3 = 1741896487  # about 400 followers
MEDIA_ID = '934625295371059186_205828054'
MEDIA_ID_2 = '806703315661297054_190931988'  # media without caption


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
        self.assertEqual(u.followers_count, followers.count())


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

    def test_fetch_user_media(self):
        u = UserFactory(id=USER_ID)

        medias = u.fetch_recent_media()
        m = medias[0]

        self.assertEqual(m.user, u)

        self.assertGreater(len(m.caption), 0)
        self.assertGreater(len(m.link), 0)

        self.assertGreater(m.comments_count, 0)
        self.assertGreater(m.likes_count, 0)

        self.assertGreater(m.fetched, self.time)
        self.assertIsInstance(m.created_time, datetime)

    def test_fetch_all_user_media(self):
        u = User.remote.fetch(USER_ID_2)
        medias = u.fetch_recent_media(all=True)

        self.assertGreater(u.media_count, 210)
        self.assertEqual(u.media_count, medias.count())
        self.assertEqual(u.media_count, u.media_feed.count())

    def test_fetch_comments(self):
        m = Media.remote.fetch(MEDIA_ID)

        comments = m.fetch_comments()

        self.assertGreater(m.comments_count, 0)
        self.assertEqual(m.comments_count, len(comments)) # TODO: strange bug of API

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


