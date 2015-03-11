# -*- coding: utf-8 -*-
from django.test import TestCase
from . models import User, Media, Comment
#from .factories import UserFactory, MediaFactory

USER_ID = 237074561 # tnt_online
MEDIA_ID = '934625295371059186_205828054'



class UserTest(TestCase):

    def test_fetch_user(self):
        u = User.remote.fetch(USER_ID)

        self.assertEqual(int(u.id), USER_ID)
        self.assertEqual(u.username, 'tnt_online')
        self.assertEqual(u.full_name, u'Телеканал ТНТ')

        self.assertGreater(len(u.profile_picture), 0)
        self.assertGreater(len(u.website), 0)
        self.assertGreater(u.followers_count, 0)
        self.assertGreater(u.media_count, 0)


class MediaTest(TestCase):

    def test_fetch_media(self):
        m = Media.remote.fetch(MEDIA_ID)

        self.assertEqual(m.id, MEDIA_ID)
        #self.assertGreater(len(m.caption), 0)
        self.assertGreater(len(m.link), 0)
        self.assertGreater(m.comment_count, 0)
        self.assertGreater(m.like_count, 0)

    def test_fetch_comments(self):
        m = Media.remote.fetch(MEDIA_ID)

        comments = m.fetch_comments()

        self.assertGreater(m.comment_count, 0)
        self.assertEqual(m.comment_count, len(comments))

    def test_fetch_likes(self):
        m = Media.remote.fetch(MEDIA_ID)

        likes = m.fetch_likes()

        self.assertGreater(m.like_count, 0)
        self.assertEqual(m.like_count, len(likes)) # TODO: get all likes



