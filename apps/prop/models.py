import os
import hashlib

from django.conf import settings
from django.db import models
from django.utils import timezone
from reversion import revisions as reversion
from django.dispatch import receiver
from django.db.models.signals import post_delete, post_save
from django.contrib.auth import get_user_model

from .middleware import get_current_county_id, clear_county_cached
from project.helpers.utils import get_random_upload_path

User = get_user_model()


def avatar_file_path_func(instance, filename):
    return get_random_upload_path(os.path.join('uploads', 'profile_avatar'), filename)


class UserProfile(models.Model):
    GENDER_UNKNOWN = 'u'
    GENDER_MALE = 'm'
    GENDER_FEMALE = 'f'
    GENDER_CHOICES = (
        (GENDER_UNKNOWN, 'Unknown'),
        (GENDER_MALE, 'Male'),
        (GENDER_FEMALE, 'Female'),
    )

    user = models.OneToOneField(settings.AUTH_USER_MODEL, primary_key=True, related_name='profile',
                                on_delete=models.CASCADE)
    birth_date = models.DateField('Date of birth', blank=True, null=True)
    gender = models.CharField('Gender', max_length=1, choices=GENDER_CHOICES, default=GENDER_UNKNOWN)
    avatar = models.ImageField('Avatar', blank=True, null=True, upload_to=avatar_file_path_func)


@receiver(post_save, sender=User)
def create_user_profile(sender, instance, created, **kwargs):
    if created:
        UserProfile.objects.create(user=instance)


@receiver(post_save, sender=User)
def save_user_profile(sender, instance, **kwargs):
    try:
        profile = instance.profile
    except UserProfile.DoesNotExist:
        profile = UserProfile.objects.create(user=instance)
    profile.save()


class County(models.Model):
    name = models.CharField(max_length=128, unique=True)
    display_name = models.CharField(max_length=255, blank=True, null=True)
    active = models.BooleanField(default=True)

    class Meta:
        verbose_name = "County"
        verbose_name_plural = "Counties"

    def save(self, *args, **kwargs):
        if self.name:
            self.name = self.name.lower()
        return super(County, self).save(*args, **kwargs)

    def __str__(self):
        return self.name


class CountyBaseModel(models.Model):
    """
    Top level entity, each entity will be linked to one,
    which might have one or more Users registered.
    Those Users are added through the admin interface.
    """
    county = models.ForeignKey(County, on_delete=models.CASCADE, default=get_current_county_id)

    class Meta:
        abstract = True


@reversion.register()
class Property(CountyBaseModel):
    parid = models.CharField(max_length=255)
    timestamp = models.DateTimeField(default=timezone.now)

    def __str__(self):
        return self.parid

    class Meta:
        unique_together = ("parid", "county")


@reversion.register()
class Owner(CountyBaseModel):
    """
    This is a list of all owners
    Jeffco ASTP600 file:
        OWNNAM
        OWNNAM2
        OWNNAM3
        OWNICO
        DBA
    """
    # First and last or company and DBA
    name = models.CharField(max_length=255)
    dba = models.BooleanField(default=False)
    ownico = models.BooleanField(default=False)
    # Maybe use for DBA flag, Care of flag...
    other = models.CharField(max_length=255, default=None, null=True)
    timestamp = models.DateTimeField(default=timezone.now)
    properties = models.ManyToManyField(Property, default=list, blank=True)

    def __str__(self):
        return self.name


class Address(CountyBaseModel):
    """
    All addresses, owner (mailing) and property
    """
    TIGET_SIDE_LEFT = 'L'
    TIGET_SIDE_RIGHT = 'R'
    TIGET_SIDES_CHOICES = (
        (TIGET_SIDE_LEFT, 'Left'),
        (TIGET_SIDE_RIGHT, 'Right'),
    )
    street1 = models.CharField(max_length=255, default=None, null=True)
    street2 = models.CharField(max_length=255, default=None, null=True)
    city = models.CharField(max_length=255, default=None, null=True)
    state = models.CharField(max_length=255, default=None, null=True)
    zipcode = models.CharField(max_length=15, default=None, null=True)
    zip4 = models.CharField(max_length=15, default=None, null=True)
    standardized = models.CharField(max_length=255, default=None, null=True)
    tiger_line_id = models.CharField(max_length=16, default=None, null=True)
    tiger_line_side = models.CharField(max_length=1, default=None, null=True,
                                       choices=TIGET_SIDES_CHOICES)
    timestamp = models.DateTimeField(default=timezone.now)

    _hashit = hashlib.sha256

    def addresshasher(self):
        """
        mash together the address values
        """
        values = (self.street1, self.street2, self.city, self.state, self.zipcode, self.zip4)
        h = ''.join(str(a).upper().replace(' ', '')
                    for a in values if a is not None).lstrip('0')
        if not h:
            return None

        county_id = self.county_id or (self.county and self.county.id)
        if county_id:
            h = '{}{}'.format(h, county_id)
        return self._hashit(h.encode('u8')).hexdigest()

    def save(self, *args, **kwargs):
        self.idhash = self.addresshasher()
        super(Address, self).save(*args, **kwargs)

    def __str__(self):
        return '{}'.format(self.street1 or self.street2)

    class Meta:
        abstract = True


@reversion.register()
class PropertyAddress(Address):
    """
    All Property Address
    """
    idhash = models.CharField(max_length=128, editable=False, null=True)
    property = models.OneToOneField(Property, on_delete=models.CASCADE,
                                    unique=True, related_name='address')

    class Meta:
        unique_together = ('idhash', 'property')


@reversion.register()
class OwnerAddress(Address):
    """
    All Owner (Mailing) Address
    """
    idhash = models.CharField(max_length=128, editable=False, null=True)
    owner = models.ForeignKey(Owner, on_delete=models.CASCADE,
                              related_name='addresses')

    class Meta:
        unique_together = ('idhash', 'owner')


class Account(CountyBaseModel):
    property = models.ForeignKey(Property, on_delete=models.CASCADE)
    tax_year = models.IntegerField(default=None, null=False)
    tax_type = models.CharField(max_length=64)
    effective_date = models.DateField(null=False)
    amount = models.DecimalField(max_digits=12, decimal_places=2, null=False)
    balance = models.DecimalField(max_digits=12, decimal_places=2, null=False)
    timestamp = models.DateTimeField(default=timezone.now)

    def __str__(self):
        return 'Account(tax_year={0}, amount={1})'.format(self.tax_year,
                                                          self.amount)


class LienAuction(CountyBaseModel):
    property = models.ForeignKey(Property, on_delete=models.CASCADE)
    face_value = models.DecimalField(max_digits=12, decimal_places=2)
    name = models.CharField(max_length=255)
    tax_year = models.IntegerField()
    winning_bid = models.DecimalField(max_digits=12, decimal_places=2, null=True)
    timestamp = models.DateTimeField(default=timezone.now)

    def __str__(self):
        return 'LienAuction(tax_year={0}, winning_bid={1})'.format(
            self.tax_year, self.winning_bid)

    class Meta:
        unique_together = ('property', 'tax_year')


@receiver(post_save, sender=County)
@receiver(post_delete, sender=County)
def clear_ip_range_cache(sender, instance, *args, **kwargs):
    clear_county_cached(instance.name)
