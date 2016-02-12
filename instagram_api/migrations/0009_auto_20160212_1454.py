# -*- coding: utf-8 -*-
from __future__ import unicode_literals

from django.db import models, migrations


class Migration(migrations.Migration):

    dependencies = [
        ('instagram_api', '0008_auto_20160212_1345'),
    ]

    operations = [
        migrations.RemoveField(
            model_name='media',
            name='locations',
        ),
        migrations.AddField(
            model_name='media',
            name='location',
            field=models.ForeignKey(related_name='media_feed', to='instagram_api.Location', null=True),
            preserve_default=True,
        ),
    ]
