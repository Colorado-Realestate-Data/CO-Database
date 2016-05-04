# -*- coding: utf-8 -*-
# Generated by Django 1.9.5 on 2016-05-04 15:01
from __future__ import unicode_literals

from django.db import migrations, models


class Migration(migrations.Migration):

    dependencies = [
        ('prop', '0001_initial'),
    ]

    operations = [
        migrations.AlterField(
            model_name='owneraddress',
            name='idhash',
            field=models.CharField(editable=False, max_length=128),
        ),
        migrations.AlterUniqueTogether(
            name='owneraddress',
            unique_together=set([('idhash', 'owner')]),
        ),
    ]
