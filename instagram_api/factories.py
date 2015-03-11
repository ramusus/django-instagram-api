from django.utils import timezone
import random

import factory
import models


class UserFactory(factory.DjangoModelFactory):

    id = factory.Sequence(lambda n: n)
    username = factory.Sequence(lambda n: n)
    full_name = factory.Sequence(lambda n: n)
    bio = factory.Sequence(lambda n: n)

    followers_count = factory.LazyAttribute(lambda o: random.randint(0, 1000))

    class Meta:
        model = models.User


class MediaFactory(factory.DjangoModelFactory):

    id = factory.Sequence(lambda n: n)

    user = factory.SubFactory(UserFactory)
    comment_count = factory.LazyAttribute(lambda o: random.randint(0, 1000))
    like_count = factory.LazyAttribute(lambda o: random.randint(0, 1000))

    class Meta:
        model = models.Media
