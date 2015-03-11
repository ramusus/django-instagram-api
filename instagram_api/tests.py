# -*- coding: utf-8 -*-
from django.test import TestCase
from . models import User, Media, Comment


MEDIA_ID = '934625295371059186_205828054'



class MediaTest(TestCase):

    def test_fetch_media(self):
        m = Media.remote.fetch(MEDIA_ID)

        self.assertEqual(m.id, MEDIA_ID)
        #self.assertGreater(len(m.caption), 0)
        self.assertGreater(len(m.link), 0)
        self.assertGreater(m.comment_count, 0)
        self.assertGreater(m.like_count, 0)
