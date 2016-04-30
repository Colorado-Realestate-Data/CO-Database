from django.db import models
from datetime import datetime


class Property(models.Model):
    parid = models.CharField(max_length=255)
    county = models.CharField(max_length=255)
    timestamp = models.DateTimeField(default=datetime.now)

    def __str__(self):
        return self.parid

    class Meta:
        unique_together = (("parid", "county"),)


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
    idhash = models.CharField(max_length=1024, unique=True)
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

    def __str__(self):
        return '{}'.format(self.street1 or self.street2)

    class Meta:
        abstract = True


class PropertyAddress(Address):
    """
    All Property Address
    """
    property = models.OneToOneField(Property, on_delete=models.CASCADE,
                                    unique=True, related_name='address')


class OwnerAddress(Address):
    """
    All Owner (Mailing) Address
    """
    owner = models.ForeignKey(Owner, on_delete=models.CASCADE,
                              related_name='addresses')


# class Account(models.Model):
#     property = models.ForeignKey(Property, related_name='account')
#     tax_year = models.IntegerField()
#     tax_type = models.CharField(max_length=64)
#     effective_date = models.DateField(null=True)
#     amount = models.FloatField()
#     balance = models.FloatField()
#     timestamp = models.DateTimeField(default=datetime.now)


# class LienAuction(models.Model):
#     property = models.ForeignKey(Property, related_name='lien_auction')
#     face_value = models.FloatField()
#     name = models.CharField(max_length=255)
#     tax_year = models.IntegerField()
#     winning_bid = models.FloatField()
#     timestamp = models.DateTimeField(default=datetime.now)
