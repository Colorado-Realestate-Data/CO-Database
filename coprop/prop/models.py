import hashlib
from django.db import models
from datetime import datetime
from reversion import revisions as reversion


@reversion.register()
class Property(models.Model):
    parid = models.CharField(max_length=255)
    county = models.CharField(max_length=255)
    timestamp = models.DateTimeField(default=datetime.now)

    def __str__(self):
        return self.parid

    class Meta:
        unique_together = (("parid", "county"),)


@reversion.register()
class Owner(models.Model):
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
    timestamp = models.DateTimeField(default=datetime.now)
    properties = models.ManyToManyField(Property, default=list, blank=True)

    def __str__(self):
        return self.name


class Address(models.Model):
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
    zipcode = models.IntegerField(default=None, null=True)
    zip4 = models.IntegerField(default=None, null=True)
    standardized = models.CharField(max_length=255, default=None, null=True)
    tiger_line_id = models.CharField(max_length=16, default=None, null=True)
    tiger_line_side = models.CharField(max_length=1, default=None, null=True,
                                       choices=TIGET_SIDES_CHOICES)
    timestamp = models.DateTimeField(default=datetime.now)

    _hashit = hashlib.sha256

    def addresshasher(self):
        """
        mash together the address values
        """
        values = (self.street1, self.street2, self.city, self.state,
                  self.zipcode, self.zip4)
        h = ''.join(str(a).upper().replace(' ', '')
                    for a in values if a is not None).lstrip('0')
        h = self._hashit(h.encode('u8')).hexdigest()
        return h

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
    idhash = models.CharField(max_length=128, unique=True, editable=False)
    property = models.OneToOneField(Property, on_delete=models.CASCADE,
                                    unique=True, related_name='address')


@reversion.register()
class OwnerAddress(Address):
    """
    All Owner (Mailing) Address
    """
    idhash = models.CharField(max_length=128, editable=False)
    owner = models.ForeignKey(Owner, on_delete=models.CASCADE,
                              related_name='addresses')

    class Meta:
        unique_together = ('idhash', 'owner')


class Account(models.Model):
    property = models.ForeignKey(Property)
    tax_year = models.IntegerField(default=None, null=False)
    tax_type = models.CharField(max_length=64)
    effective_date = models.DateField(null=False)
    amount = models.DecimalField(max_digits=12, decimal_places=2, null=False)
    balance = models.DecimalField(max_digits=12, decimal_places=2, null=False)
    timestamp = models.DateTimeField(default=datetime.now)

    def __str__(self):
        return 'Account(tax_year={0}, amount={1})'.format(self.tax_year,
                                                          self.amount)

    class Meta:
        unique_together = ('property', 'tax_year', 'tax_type',
                           'effective_date', 'amount', 'balance')


class LienAuction(models.Model):
    property = models.ForeignKey(Property)
    face_value = models.DecimalField(max_digits=12, decimal_places=2)
    name = models.CharField(max_length=255)
    tax_year = models.IntegerField()
    winning_bid = models.DecimalField(max_digits=12, decimal_places=2)
    timestamp = models.DateTimeField(default=datetime.now)

    def __str__(self):
        return 'LienAuction(tax_year={0}, winning_bid={1})'.format(
            self.tax_year, self.winning_bid)

    class Meta:
        unique_together = ('property', 'tax_year')
