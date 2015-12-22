# -*- coding: utf-8 -*-
from __future__ import unicode_literals

from django.db import models, migrations


class Migration(migrations.Migration):

    dependencies = [
        ('instagram_api', '0002_user_follows_count'),
    ]

    operations = [
        migrations.AddField(
            model_name='user',
            name='is_private',
            field=models.NullBooleanField(verbose_name=b'Account is private'),
            preserve_default=True,
        ),
    ]
