# -*- coding: utf-8 -*-
from __future__ import unicode_literals

from django.db import models, migrations


class Migration(migrations.Migration):

    dependencies = [
        ('instagram_api', '0005_auto_20160212_0204'),
    ]

    operations = [
        migrations.AddField(
            model_name='media',
            name='filter',
            field=models.CharField(default='', max_length=40),
            preserve_default=False,
        ),
    ]
