# -*- coding: utf-8 -*-
# Generated by Django 1.11.2 on 2017-07-15 12:17
from __future__ import unicode_literals

from django.db import migrations


class Migration(migrations.Migration):

    dependencies = [
        ('prop', '0005_auto_20170714_0427'),
    ]

    operations = [
        migrations.AlterUniqueTogether(
            name='account',
            unique_together=set([]),
        ),
    ]
