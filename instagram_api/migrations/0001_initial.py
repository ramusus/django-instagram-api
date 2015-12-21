# -*- coding: utf-8 -*-
from __future__ import unicode_literals

from django.db import models, migrations
import m2m_history.fields


class Migration(migrations.Migration):

    dependencies = [
    ]

    operations = [
        migrations.CreateModel(
            name='Comment',
            fields=[
                ('fetched', models.DateTimeField(null=True, verbose_name='Fetched', blank=True)),
                ('id', models.BigIntegerField(serialize=False, primary_key=True)),
                ('text', models.TextField()),
                ('created_time', models.DateTimeField()),
            ],
            options={
                'abstract': False,
            },
            bases=(models.Model,),
        ),
        migrations.CreateModel(
            name='Media',
            fields=[
                ('id', models.AutoField(verbose_name='ID', serialize=False, auto_created=True, primary_key=True)),
                ('fetched', models.DateTimeField(null=True, verbose_name='Fetched', blank=True)),
                ('remote_id', models.CharField(unique=True, max_length=100)),
                ('caption', models.TextField(blank=True)),
                ('link', models.URLField(max_length=300)),
                ('type', models.CharField(max_length=20)),
                ('image_low_resolution', models.URLField()),
                ('image_standard_resolution', models.URLField()),
                ('image_thumbnail', models.URLField()),
                ('video_low_bandwidth', models.URLField()),
                ('video_low_resolution', models.URLField()),
                ('video_standard_resolution', models.URLField()),
                ('created_time', models.DateTimeField()),
                ('comments_count', models.PositiveIntegerField(null=True)),
                ('likes_count', models.PositiveIntegerField(null=True)),
            ],
            options={
                'abstract': False,
            },
            bases=(models.Model,),
        ),
        migrations.CreateModel(
            name='Tag',
            fields=[
                ('id', models.AutoField(verbose_name='ID', serialize=False, auto_created=True, primary_key=True)),
                ('fetched', models.DateTimeField(null=True, verbose_name='Fetched', blank=True)),
                ('name', models.CharField(unique=True, max_length=29)),
                ('media_count', models.PositiveIntegerField(null=True)),
                ('media_feed', models.ManyToManyField(related_name='tags', to='instagram_api.Media')),
            ],
            options={
                'abstract': False,
            },
            bases=(models.Model,),
        ),
        migrations.CreateModel(
            name='User',
            fields=[
                ('fetched', models.DateTimeField(null=True, verbose_name='Fetched', blank=True)),
                ('id', models.BigIntegerField(serialize=False, primary_key=True)),
                ('username', models.CharField(unique=True, max_length=50)),
                ('full_name', models.CharField(max_length=255)),
                ('bio', models.CharField(max_length=255, verbose_name=b'BIO')),
                ('profile_picture', models.URLField(max_length=300)),
                ('website', models.URLField(max_length=300)),
                ('followers_count', models.PositiveIntegerField(null=True)),
                ('media_count', models.PositiveIntegerField(null=True)),
                ('followers', m2m_history.fields.ManyToManyHistoryField(to='instagram_api.User')),
            ],
            options={
                'abstract': False,
            },
            bases=(models.Model,),
        ),
        migrations.AddField(
            model_name='media',
            name='likes_users',
            field=m2m_history.fields.ManyToManyHistoryField(related_name='likes_media', to='instagram_api.User'),
            preserve_default=True,
        ),
        migrations.AddField(
            model_name='media',
            name='user',
            field=models.ForeignKey(related_name='media_feed', to='instagram_api.User'),
            preserve_default=True,
        ),
        migrations.AddField(
            model_name='comment',
            name='media',
            field=models.ForeignKey(related_name='comments', to='instagram_api.Media'),
            preserve_default=True,
        ),
        migrations.AddField(
            model_name='comment',
            name='owner',
            field=models.ForeignKey(related_name='media_comments', to='instagram_api.User'),
            preserve_default=True,
        ),
        migrations.AddField(
            model_name='comment',
            name='user',
            field=models.ForeignKey(related_name='comments', to='instagram_api.User'),
            preserve_default=True,
        ),
    ]
