# -*- coding: utf-8 -*-
# Generated by Django 1.11.6 on 2017-11-09 20:17
from __future__ import unicode_literals

from django.db import migrations, models
import django.db.models.deletion


class Migration(migrations.Migration):

    dependencies = [
        ('api', '0006_auto_20171108_1720'),
    ]

    operations = [
        migrations.AddField(
            model_name='event',
            name='owner',
            field=models.ForeignKey(default=None, on_delete=django.db.models.deletion.CASCADE, to='api.Participant'),
            preserve_default=False,
        ),
        migrations.AlterField(
            model_name='question',
            name='event',
            field=models.ForeignKey(on_delete=django.db.models.deletion.CASCADE, related_name='questions', to='api.Event'),
        ),
    ]
