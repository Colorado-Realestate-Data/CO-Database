from django.db import models
from datetime import datetime


class Property(models.Model):
    uid = models.CharField(max_length=64, unique=True)
    parid = models.CharField(max_length=255, null=True)
    county = models.CharField(max_length=255)
    timestamp = models.DateTimeField(default=datetime.now)

    def __str__(self):
        return self.uid

    class Meta:
        index_together = (("uid", "county"),)


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
    properties = models.ManyToManyField(Property)

    def __str__(self):
        return self.name


class Address(models.Model):
    """
    All addresses, owner (mailing) and property
    """
    idhash = models.CharField(max_length=1024, unique=True)
    street1 = models.CharField(max_length=255, default=None, null=True)
    street2 = models.CharField(max_length=255, default=None, null=True)
    city = models.CharField(max_length=255, default=None, null=True)
    state = models.CharField(max_length=255, default=None, null=True)
    zipcode = models.IntegerField(default=None, null=True)
    zip4 = models.IntegerField(default=None, null=True)
    timestamp = models.DateTimeField(default=datetime.now)

    def __str__(self):
        return self.street1 or self.street2

    class Meta:
        abstract = True


class PropertyAddress(Address):
    """
    All Property Address
    """
    property = models.OneToOneField(Property, on_delete=models.CASCADE,
                                    primary_key=True)


class OwnerAddress(Address):
    """
    All Owner (Mailing) Address
    """
    owner = models.ForeignKey(Owner, on_delete=models.CASCADE)


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
