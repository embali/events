# -*- coding: utf-8 -*-
from __future__ import unicode_literals

from django.db import models, migrations
import django.db.models.deletion


class Migration(migrations.Migration):

    dependencies = [
    ]

    operations = [
        migrations.CreateModel(
            name='Event',
            fields=[
                ('id', models.AutoField(verbose_name='ID', serialize=False, auto_created=True, primary_key=True)),
                ('title', models.CharField(max_length=64)),
                ('topic', models.CharField(max_length=128, null=True, blank=True)),
                ('start_date', models.DateTimeField()),
                ('end_date', models.DateTimeField()),
                ('person_in_charge', models.CharField(max_length=64, null=True, blank=True)),
                ('is_inhouse', models.BooleanField(default=True)),
                ('location_name_ext', models.CharField(max_length=64, null=True, blank=True)),
                ('location_building_ext', models.CharField(max_length=65, null=True, blank=True)),
                ('location_room_ext', models.CharField(max_length=16, null=True, blank=True)),
                ('location_contact_ext', models.CharField(max_length=128, null=True, blank=True)),
                ('full_description', models.TextField()),
                ('short_description', models.CharField(max_length=256, null=True, blank=True)),
                ('notes', models.TextField()),
                ('casy_ref', models.IntegerField()),
            ],
            options={
            },
            bases=(models.Model,),
        ),
        migrations.CreateModel(
            name='EventType',
            fields=[
                ('id', models.AutoField(verbose_name='ID', serialize=False, auto_created=True, primary_key=True)),
                ('name', models.CharField(unique=True, max_length=32)),
                ('title', models.CharField(max_length=128)),
                ('is_active', models.BooleanField(default=True)),
                ('allow_internal_registrations', models.BooleanField(default=True)),
                ('allow_external_registrations', models.BooleanField(default=True)),
                ('has_speakers', models.BooleanField(default=False)),
                ('has_topic', models.BooleanField(default=False)),
            ],
            options={
            },
            bases=(models.Model,),
        ),
        migrations.CreateModel(
            name='Location',
            fields=[
                ('id', models.AutoField(verbose_name='ID', serialize=False, auto_created=True, primary_key=True)),
                ('name', models.CharField(unique=True, max_length=64)),
            ],
            options={
            },
            bases=(models.Model,),
        ),
        migrations.CreateModel(
            name='Speaker',
            fields=[
                ('id', models.AutoField(verbose_name='ID', serialize=False, auto_created=True, primary_key=True)),
                ('casy_ref', models.IntegerField(unique=True)),
                ('bio', models.TextField()),
            ],
            options={
            },
            bases=(models.Model,),
        ),
        migrations.AddField(
            model_name='event',
            name='location_name_int',
            field=models.ForeignKey(to='events.Location', null=True),
            preserve_default=True,
        ),
        migrations.AddField(
            model_name='event',
            name='speakers',
            field=models.ManyToManyField(to='events.Speaker'),
            preserve_default=True,
        ),
        migrations.AddField(
            model_name='event',
            name='type',
            field=models.ForeignKey(to='events.EventType', on_delete=django.db.models.deletion.PROTECT),
            preserve_default=True,
        ),
    ]
