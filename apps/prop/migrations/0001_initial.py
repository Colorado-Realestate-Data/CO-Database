# Generated by Django 2.0 on 2018-01-06 09:06

import apps.prop.middleware
import apps.prop.models
from django.conf import settings
from django.db import migrations, models
import django.db.models.deletion
import django.utils.timezone


class Migration(migrations.Migration):

    initial = True

    dependencies = [
        ('auth', '0009_alter_user_last_name_max_length'),
    ]

    operations = [
        migrations.CreateModel(
            name='Account',
            fields=[
                ('id', models.AutoField(auto_created=True, primary_key=True, serialize=False, verbose_name='ID')),
                ('tax_year', models.IntegerField(default=None)),
                ('tax_type', models.CharField(max_length=64)),
                ('effective_date', models.DateField()),
                ('amount', models.DecimalField(decimal_places=2, max_digits=12)),
                ('balance', models.DecimalField(decimal_places=2, max_digits=12)),
                ('timestamp', models.DateTimeField(default=django.utils.timezone.now)),
            ],
            options={
                'abstract': False,
            },
        ),
        migrations.CreateModel(
            name='County',
            fields=[
                ('id', models.AutoField(auto_created=True, primary_key=True, serialize=False, verbose_name='ID')),
                ('name', models.CharField(max_length=128, unique=True)),
                ('display_name', models.CharField(blank=True, max_length=255, null=True)),
                ('active', models.BooleanField(default=True)),
            ],
            options={
                'verbose_name': 'County',
                'verbose_name_plural': 'Counties',
            },
        ),
        migrations.CreateModel(
            name='LienAuction',
            fields=[
                ('id', models.AutoField(auto_created=True, primary_key=True, serialize=False, verbose_name='ID')),
                ('face_value', models.DecimalField(decimal_places=2, max_digits=12)),
                ('name', models.CharField(max_length=255)),
                ('tax_year', models.IntegerField()),
                ('winning_bid', models.DecimalField(decimal_places=2, max_digits=12, null=True)),
                ('timestamp', models.DateTimeField(default=django.utils.timezone.now)),
                ('county', models.ForeignKey(default=apps.prop.middleware.get_current_county_id, on_delete=django.db.models.deletion.CASCADE, to='prop.County')),
            ],
        ),
        migrations.CreateModel(
            name='Owner',
            fields=[
                ('id', models.AutoField(auto_created=True, primary_key=True, serialize=False, verbose_name='ID')),
                ('name', models.CharField(max_length=255)),
                ('dba', models.BooleanField(default=False)),
                ('ownico', models.BooleanField(default=False)),
                ('other', models.CharField(default=None, max_length=255, null=True)),
                ('timestamp', models.DateTimeField(default=django.utils.timezone.now)),
                ('county', models.ForeignKey(default=apps.prop.middleware.get_current_county_id, on_delete=django.db.models.deletion.CASCADE, to='prop.County')),
            ],
            options={
                'abstract': False,
            },
        ),
        migrations.CreateModel(
            name='OwnerAddress',
            fields=[
                ('id', models.AutoField(auto_created=True, primary_key=True, serialize=False, verbose_name='ID')),
                ('street1', models.CharField(default=None, max_length=255, null=True)),
                ('street2', models.CharField(default=None, max_length=255, null=True)),
                ('city', models.CharField(default=None, max_length=255, null=True)),
                ('state', models.CharField(default=None, max_length=255, null=True)),
                ('zipcode', models.CharField(default=None, max_length=15, null=True)),
                ('zip4', models.CharField(default=None, max_length=15, null=True)),
                ('standardized', models.CharField(default=None, max_length=255, null=True)),
                ('tiger_line_id', models.CharField(default=None, max_length=16, null=True)),
                ('tiger_line_side', models.CharField(choices=[('L', 'Left'), ('R', 'Right')], default=None, max_length=1, null=True)),
                ('timestamp', models.DateTimeField(default=django.utils.timezone.now)),
                ('idhash', models.CharField(editable=False, max_length=128, null=True)),
                ('county', models.ForeignKey(default=apps.prop.middleware.get_current_county_id, on_delete=django.db.models.deletion.CASCADE, to='prop.County')),
                ('owner', models.ForeignKey(on_delete=django.db.models.deletion.CASCADE, related_name='addresses', to='prop.Owner')),
            ],
        ),
        migrations.CreateModel(
            name='Property',
            fields=[
                ('id', models.AutoField(auto_created=True, primary_key=True, serialize=False, verbose_name='ID')),
                ('parid', models.CharField(max_length=255)),
                ('timestamp', models.DateTimeField(default=django.utils.timezone.now)),
                ('county', models.ForeignKey(default=apps.prop.middleware.get_current_county_id, on_delete=django.db.models.deletion.CASCADE, to='prop.County')),
            ],
        ),
        migrations.CreateModel(
            name='PropertyAddress',
            fields=[
                ('id', models.AutoField(auto_created=True, primary_key=True, serialize=False, verbose_name='ID')),
                ('street1', models.CharField(default=None, max_length=255, null=True)),
                ('street2', models.CharField(default=None, max_length=255, null=True)),
                ('city', models.CharField(default=None, max_length=255, null=True)),
                ('state', models.CharField(default=None, max_length=255, null=True)),
                ('zipcode', models.CharField(default=None, max_length=15, null=True)),
                ('zip4', models.CharField(default=None, max_length=15, null=True)),
                ('standardized', models.CharField(default=None, max_length=255, null=True)),
                ('tiger_line_id', models.CharField(default=None, max_length=16, null=True)),
                ('tiger_line_side', models.CharField(choices=[('L', 'Left'), ('R', 'Right')], default=None, max_length=1, null=True)),
                ('timestamp', models.DateTimeField(default=django.utils.timezone.now)),
                ('idhash', models.CharField(editable=False, max_length=128, null=True)),
                ('county', models.ForeignKey(default=apps.prop.middleware.get_current_county_id, on_delete=django.db.models.deletion.CASCADE, to='prop.County')),
                ('property', models.OneToOneField(on_delete=django.db.models.deletion.CASCADE, related_name='address', to='prop.Property')),
            ],
        ),
        migrations.CreateModel(
            name='UserProfile',
            fields=[
                ('user', models.OneToOneField(on_delete=django.db.models.deletion.CASCADE, primary_key=True, related_name='profile', serialize=False, to=settings.AUTH_USER_MODEL)),
                ('birth_date', models.DateField(blank=True, null=True, verbose_name='Date of birth')),
                ('gender', models.CharField(choices=[('u', 'Unknown'), ('m', 'Male'), ('f', 'Female')], default='u', max_length=1, verbose_name='Gender')),
                ('avatar', models.ImageField(blank=True, null=True, upload_to=apps.prop.models.avatar_file_path_func, verbose_name='Avatar')),
            ],
        ),
        migrations.AddField(
            model_name='owner',
            name='properties',
            field=models.ManyToManyField(blank=True, default=list, to='prop.Property'),
        ),
        migrations.AddField(
            model_name='lienauction',
            name='property',
            field=models.ForeignKey(on_delete=django.db.models.deletion.CASCADE, to='prop.Property'),
        ),
        migrations.AddField(
            model_name='account',
            name='county',
            field=models.ForeignKey(default=apps.prop.middleware.get_current_county_id, on_delete=django.db.models.deletion.CASCADE, to='prop.County'),
        ),
        migrations.AddField(
            model_name='account',
            name='property',
            field=models.ForeignKey(on_delete=django.db.models.deletion.CASCADE, to='prop.Property'),
        ),
        migrations.AlterUniqueTogether(
            name='propertyaddress',
            unique_together={('idhash', 'property')},
        ),
        migrations.AlterUniqueTogether(
            name='property',
            unique_together={('parid', 'county')},
        ),
        migrations.AlterUniqueTogether(
            name='owneraddress',
            unique_together={('idhash', 'owner')},
        ),
        migrations.AlterUniqueTogether(
            name='lienauction',
            unique_together={('property', 'tax_year')},
        ),
    ]
