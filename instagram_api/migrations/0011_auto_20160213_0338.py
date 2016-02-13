# -*- coding: utf-8 -*-
from __future__ import unicode_literals

from django.db import models, migrations


class Migration(migrations.Migration):

    dependencies = [
        ('instagram_api', '0010_auto_20160212_1602'),
    ]

    operations = [
        migrations.AlterField(
            model_name='media',
            name='link',
            field=models.URLField(max_length=68),
            preserve_default=True,
        ),
        migrations.AlterField(
            model_name='media',
            name='remote_id',
            field=models.CharField(unique=True, max_length=30),
            preserve_default=True,
        ),
        migrations.AlterField(
            model_name='media',
            name='type',
            field=models.CharField(max_length=5),
            preserve_default=True,
        ),
        migrations.AlterField(
            model_name='media',
            name='video_low_bandwidth',
            field=models.URLField(max_length=130),
            preserve_default=True,
        ),
        migrations.AlterField(
            model_name='media',
            name='video_low_resolution',
            field=models.URLField(max_length=130),
            preserve_default=True,
        ),
        migrations.AlterField(
            model_name='media',
            name='video_standard_resolution',
            field=models.URLField(max_length=130),
            preserve_default=True,
        ),
        migrations.AlterField(
            model_name='user',
            name='bio',
            field=models.CharField(max_length=150),
            preserve_default=True,
        ),
        migrations.AlterField(
            model_name='user',
            name='full_name',
            field=models.CharField(max_length=30),
            preserve_default=True,
        ),
        migrations.AlterField(
            model_name='user',
            name='profile_picture',
            field=models.URLField(max_length=112),
            preserve_default=True,
        ),
        migrations.AlterField(
            model_name='user',
            name='username',
            field=models.CharField(unique=True, max_length=30),
            preserve_default=True,
        ),
        migrations.AlterField(
            model_name='user',
            name='website',
            field=models.URLField(max_length=150),
            preserve_default=True,
        ),
    ]
