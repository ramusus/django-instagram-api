import random
import string

import factory
from django.utils import timezone

from . import models


class UserFactory(factory.DjangoModelFactory):

    id = factory.Sequence(lambda n: n)
    username = factory.Sequence(lambda n: "".join([random.choice(string.letters) for i in xrange(50)]))
    # full_name = factory.Sequence(lambda n: n)
    # bio = factory.Sequence(lambda n: n)

    followers_count = factory.LazyAttribute(lambda o: random.randint(0, 1000))

    class Meta:
        model = models.User


class MediaFactory(factory.DjangoModelFactory):

    remote_id = factory.Sequence(lambda n: "".join([random.choice(string.letters) for i in xrange(100)]))
    user = factory.SubFactory(UserFactory)
    comments_count = factory.LazyAttribute(lambda o: random.randint(0, 1000))
    likes_count = factory.LazyAttribute(lambda o: random.randint(0, 1000))

    created_time = factory.LazyAttribute(lambda o: timezone.now())

    class Meta:
        model = models.Media


class CommentFactory(factory.DjangoModelFactory):

    id = factory.Sequence(lambda n: n)
    owner = factory.SubFactory(UserFactory)
    user = factory.SubFactory(UserFactory)
    media = factory.SubFactory(MediaFactory)

    created_time = factory.LazyAttribute(lambda o: timezone.now())

    class Meta:
        model = models.Comment


class TagFactory(factory.DjangoModelFactory):

    id = factory.Sequence(lambda n: n)
    name = factory.Sequence(lambda n: "".join([random.choice(string.letters) for i in xrange(29)]))
    media_count = factory.LazyAttribute(lambda o: random.randint(0, 1000))

    @factory.post_generation
    def media_feed(self, create, extracted, **kwargs):
        if not create:
            # Simple build, do nothing.
            return

        if extracted:
            # A list of groups were passed in, use them
            for media in extracted:
                self.media_feed.add(media)

    class Meta:
        model = models.Tag
