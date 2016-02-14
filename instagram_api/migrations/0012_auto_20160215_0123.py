# -*- coding: utf-8 -*-
from __future__ import unicode_literals

from django.db import models, migrations


class Migration(migrations.Migration):

    dependencies = [
        ('instagram_api', '0011_auto_20160213_0338'),
    ]

    operations = [
        migrations.AlterField(
            model_name='user',
            name='followers_count',
            field=models.PositiveIntegerField(null=True, db_index=True),
            preserve_default=True,
        ),
        migrations.AlterField(
            model_name='user',
            name='follows_count',
            field=models.PositiveIntegerField(null=True, db_index=True),
            preserve_default=True,
        ),
        migrations.AlterField(
            model_name='user',
            name='is_private',
            field=models.NullBooleanField(db_index=True, verbose_name=b'Account is private'),
            preserve_default=True,
        ),
        migrations.AlterField(
            model_name='user',
            name='media_count',
            field=models.PositiveIntegerField(null=True, db_index=True),
            preserve_default=True,
        ),
    ]
