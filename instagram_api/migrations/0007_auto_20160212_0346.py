# -*- coding: utf-8 -*-
from __future__ import unicode_literals

from django.db import models, migrations


class Migration(migrations.Migration):

    dependencies = [
        ('instagram_api', '0006_media_filter'),
    ]

    operations = [
        migrations.RemoveField(
            model_name='location',
            name='media_feed',
        ),
        migrations.RemoveField(
            model_name='tag',
            name='media_feed',
        ),
        migrations.AddField(
            model_name='media',
            name='locations',
            field=models.ManyToManyField(related_name='media_feed', to='instagram_api.Location'),
            preserve_default=True,
        ),
        migrations.AddField(
            model_name='media',
            name='tags',
            field=models.ManyToManyField(related_name='media_feed', to='instagram_api.Tag'),
            preserve_default=True,
        ),
    ]
