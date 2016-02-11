# -*- coding: utf-8 -*-
from __future__ import unicode_literals

from django.db import models, migrations
import djangocms_text_ckeditor.fields


class Migration(migrations.Migration):

    dependencies = [
        ('events', '0003_auto_20151008_2010'),
    ]

    operations = [
        migrations.AlterField(
            model_name='event',
            name='full_description',
            field=djangocms_text_ckeditor.fields.HTMLField(),
            preserve_default=True,
        ),
    ]
