# -*- coding: utf-8 -*-
from __future__ import unicode_literals

from django.db import models, migrations
import filer.fields.file


class Migration(migrations.Migration):

    dependencies = [
        ('filer', '0002_auto_20150606_2003'),
        ('events', '0001_initial'),
    ]

    operations = [
        migrations.CreateModel(
            name='Attachment',
            fields=[
                ('id', models.AutoField(verbose_name='ID', serialize=False, auto_created=True, primary_key=True)),
                ('event', models.ForeignKey(related_name='attachments', to='events.Event')),
                ('file', filer.fields.file.FilerFileField(to='filer.File')),
            ],
            options={
            },
            bases=(models.Model,),
        ),
        migrations.CreateModel(
            name='ExternalReservation',
            fields=[
                ('id', models.AutoField(verbose_name='ID', serialize=False, auto_created=True, primary_key=True)),
                ('casy_ref', models.IntegerField()),
                ('is_confirmed', models.BooleanField(default=True)),
                ('comment', models.TextField()),
                ('event', models.ForeignKey(related_name='external_reservations', to='events.Event')),
            ],
            options={
                'abstract': False,
            },
            bases=(models.Model,),
        ),
        migrations.CreateModel(
            name='InternalReservation',
            fields=[
                ('id', models.AutoField(verbose_name='ID', serialize=False, auto_created=True, primary_key=True)),
                ('casy_ref', models.IntegerField()),
                ('is_confirmed', models.BooleanField(default=True)),
                ('comment', models.TextField()),
                ('event', models.ForeignKey(related_name='internal_reservations', to='events.Event')),
            ],
            options={
                'abstract': False,
            },
            bases=(models.Model,),
        ),
        migrations.AddField(
            model_name='event',
            name='is_active',
            field=models.BooleanField(default=True),
            preserve_default=True,
        ),
        migrations.AddField(
            model_name='event',
            name='seats_available',
            field=models.IntegerField(null=True),
            preserve_default=True,
        ),
        migrations.AddField(
            model_name='event',
            name='seats_for_internals_only',
            field=models.IntegerField(null=True),
            preserve_default=True,
        ),
    ]
