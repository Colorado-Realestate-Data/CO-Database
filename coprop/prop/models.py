import hashlib
from django.db import models
from django.utils import timezone
from reversion import revisions as reversion

from prop.middleware import get_current_county_id


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
    '''
    Top level entity, each entity will be linked to one,
    which might have one or more Users registered.
    Those Users are added through the admin interface.
    '''
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
        unique_together = (("parid", "county"),)


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
        values = (self.street1, self.street2, self.city, self.state,
                  self.zipcode, self.zip4)
        h = ''.join(str(a).upper().replace(' ', '')
                    for a in values if a is not None).lstrip('0')
        if not h:
            return None

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
    idhash = models.CharField(max_length=128, unique=True, editable=False,
                              null=True)
    property = models.OneToOneField(Property, on_delete=models.CASCADE,
                                    unique=True, related_name='address')


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
    property = models.ForeignKey(Property)
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
    property = models.ForeignKey(Property)
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
