# -*- coding: utf-8 -*-
from __future__ import unicode_literals

from django.db import models, migrations


class Migration(migrations.Migration):

    dependencies = [
        ('instagram_api', '0012_auto_20160215_0123'),
    ]

    operations = [
        migrations.AlterField(
            model_name='media',
            name='comments_count',
            field=models.PositiveIntegerField(default=0, null=True),
            preserve_default=True,
        ),
        migrations.AlterField(
            model_name='media',
            name='likes_count',
            field=models.PositiveIntegerField(default=0, null=True),
            preserve_default=True,
        ),
    ]
