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
