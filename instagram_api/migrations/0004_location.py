# -*- coding: utf-8 -*-
from __future__ import unicode_literals

from django.db import models, migrations


class Migration(migrations.Migration):

    dependencies = [
        ('instagram_api', '0003_user_is_private'),
    ]

    operations = [
        migrations.CreateModel(
            name='Location',
            fields=[
                ('fetched', models.DateTimeField(null=True, verbose_name='Fetched', blank=True)),
                ('id', models.BigIntegerField(serialize=False, primary_key=True)),
                ('name', models.CharField(max_length=100)),
                ('latitude', models.FloatField()),
                ('longitude', models.FloatField()),
                ('street_address', models.CharField(max_length=100)),
                ('media_count', models.PositiveIntegerField(null=True)),
                ('media_feed', models.ManyToManyField(related_name='locations', to='instagram_api.Media')),
            ],
            options={
                'abstract': False,
            },
            bases=(models.Model,),
        ),
    ]
