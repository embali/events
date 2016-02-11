# -*- coding: utf-8 -*-
from __future__ import unicode_literals

from django.db import models, migrations


class Migration(migrations.Migration):

    dependencies = [
        ('events', '0002_auto_20150924_1629'),
    ]

    operations = [
        migrations.AddField(
            model_name='attachment',
            name='title',
            field=models.CharField(default='title', max_length=128),
            preserve_default=False,
        ),
        migrations.AlterField(
            model_name='event',
            name='location_name_int',
            field=models.ForeignKey(blank=True, to='events.Location', null=True),
            preserve_default=True,
        ),
        migrations.AlterField(
            model_name='event',
            name='notes',
            field=models.TextField(null=True, blank=True),
            preserve_default=True,
        ),
        migrations.AlterField(
            model_name='event',
            name='speakers',
            field=models.ManyToManyField(to='events.Speaker', null=True, blank=True),
            preserve_default=True,
        ),
    ]
