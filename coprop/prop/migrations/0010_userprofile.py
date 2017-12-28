# -*- coding: utf-8 -*-
# Generated by Django 1.11.2 on 2017-12-08 20:49
from __future__ import unicode_literals

from django.conf import settings
from django.db import migrations, models
import django.db.models.deletion
import prop.models


class Migration(migrations.Migration):

    dependencies = [
        ('auth', '0008_alter_user_username_max_length'),
        ('prop', '0009_auto_20170719_1313'),
    ]

    operations = [
        migrations.CreateModel(
            name='UserProfile',
            fields=[
                ('user', models.OneToOneField(on_delete=django.db.models.deletion.CASCADE, primary_key=True, related_name='profile', serialize=False, to=settings.AUTH_USER_MODEL)),
                ('birth_date', models.DateField(blank=True, null=True, verbose_name='Date of birth')),
                ('gender', models.CharField(choices=[('u', 'Unknown'), ('m', 'Male'), ('f', 'Female')], default='u', max_length=1, verbose_name='Gender')),
                ('avatar', models.ImageField(blank=True, null=True, upload_to=prop.models.avatar_file_path_func, verbose_name='Avatar')),
            ],
        ),
    ]
