# -*- coding: utf-8 -*-
from __future__ import unicode_literals

from django.db import models, migrations


class Migration(migrations.Migration):

    dependencies = [
        ('instagram_api', '0001_initial'),
    ]

    operations = [
        migrations.AddField(
            model_name='user',
            name='follows_count',
            field=models.PositiveIntegerField(null=True),
            preserve_default=True,
        ),
    ]
