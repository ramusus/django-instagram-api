# -*- coding: utf-8 -*-
from __future__ import unicode_literals

from django.db import models, migrations
import m2m_history.fields


class Migration(migrations.Migration):

    dependencies = [
        ('instagram_api', '0009_auto_20160212_1454'),
    ]

    operations = [
        migrations.AlterField(
            model_name='user',
            name='followers',
            field=m2m_history.fields.ManyToManyHistoryField(related_name='follows', to='instagram_api.User'),
            preserve_default=True,
        ),
    ]
