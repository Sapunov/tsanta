# -*- coding: utf-8 -*-
# Generated by Django 1.11.6 on 2017-11-23 06:11
from __future__ import unicode_literals

from django.db import migrations, models


class Migration(migrations.Migration):

    dependencies = [
        ('api', '0009_group_repr_name'),
    ]

    operations = [
        migrations.AddField(
            model_name='group',
            name='searchable',
            field=models.BooleanField(default=False),
        ),
    ]
