import inspect
import sys
from rest_framework import serializers
from django.conf import settings
from rest_framework.reverse import reverse
from django.db import IntegrityError, transaction

from prop.models import Property, Owner, PropertyAddress, OwnerAddress, \
    Account, LienAuction, CountyBaseModel, County, UserProfile, User
from coprop.helpers.utils import Base64ImageField


class AvatarSerializer(serializers.ModelSerializer):
    avatar = Base64ImageField()
    class Meta:
        model = UserProfile
        fields = ('avatar',)


class NestedProfileSerializer(serializers.ModelSerializer):
    class Meta:
        model = UserProfile
        fields = ('birth_date', 'gender', 'avatar')
        read_only_fields = ('avatar', )


class UserSerializer(serializers.ModelSerializer):
    profile = NestedProfileSerializer()

    class Meta:
        model = User
        fields = ("id", "last_login", "is_superuser", "username", "first_name", "last_name", "email", "is_staff",
                  "is_active", "date_joined", "groups", "user_permissions", "profile")


class UserProfileSerializer(serializers.ModelSerializer):
    profile = NestedProfileSerializer()
    class Meta:
        model = User
        fields = ('first_name', 'last_name', 'email', 'profile', )

    def update(self, instance, validated_data):
        profile = validated_data.pop('profile', {}) or {}
        for k, v in profile.items():
            setattr(instance.profile, k, v)
        return super(UserProfileSerializer, self).update(instance, validated_data)


class SessionSerializer(serializers.Serializer):
    username = serializers.CharField(max_length=30)
    password = serializers.CharField(max_length=128)


class CountySerializer(serializers.ModelSerializer):
    api_url = serializers.SerializerMethodField('api_root_url')

    def api_root_url(self, obj):
        COUNTY_BASE_ENDPOINT_PARAM = getattr(settings, 'COUNTY_BASE_ENDPOINT_PARAM', 'county')
        VERSION_PARAM = settings.REST_FRAMEWORK.get('VERSION_PARAM', 'version')
        DEFAULT_VERSION = settings.REST_FRAMEWORK.get('DEFAULT_VERSION', 'v1')
        version = DEFAULT_VERSION
        request = self.context.get("request")
        if request:
            version = getattr(request, VERSION_PARAM, DEFAULT_VERSION) or DEFAULT_VERSION
        url = reverse('county_base_rest_api:api-root',
                      kwargs={COUNTY_BASE_ENDPOINT_PARAM: obj.name, VERSION_PARAM: version}, request=request)
        return url

    class Meta:
        model = County
        fields = '__all__'


class OwnerAddressSerializer(serializers.ModelSerializer):
    class Meta:
        model = OwnerAddress
        fields = '__all__'


class NestedOwnerAddressSerializer(serializers.ModelSerializer):
    id = serializers.IntegerField(read_only=False, required=False,
                                  allow_null=True)

    class Meta:
        model = OwnerAddress
        exclude = ('owner',)


class PropertyAddressSerializer(serializers.ModelSerializer):

    class Meta:
        model = PropertyAddress
        fields = '__all__'


class NestedPropertyAddressSerializer(serializers.ModelSerializer):

    class Meta:
        model = PropertyAddress
        exclude = ('property',)


class PropertySerializer(serializers.ModelSerializer):

    address = NestedPropertyAddressSerializer(required=False, allow_null=True)

    class Meta:
        model = Property
        fields = '__all__'

    @transaction.atomic()
    def create(self, validated_data):
        address_data = validated_data.pop('address', None)
        try:
            instance = super(PropertySerializer, self).create(validated_data)
        except IntegrityError:
            raise serializers.ValidationError({'property': {
                'parid': ["Prperty with this parid already exists."]
            }})
        if address_data:
            try:
                PropertyAddress.objects.create(property=instance,
                                               **address_data)
            except IntegrityError:
                raise serializers.ValidationError({'address': {
                    'idhash': ["Address with this idhash already exists."]
                    }})

        return instance

    @transaction.atomic()
    def update(self, instance, validated_data):
        if 'address' in validated_data:
            address_data = validated_data.pop('address')
            address = getattr(instance, 'address', None)
            if address_data:
                try:
                    if not address:
                        address_data['property'] = instance
                        PropertyAddress.objects.create(**address_data)
                    else:
                        for attr, value in address_data.items():
                            setattr(address, attr, value)
                        address.save()
                except IntegrityError:
                    raise serializers.ValidationError({'address': {
                        'idhash': ["Address with this idhash already exists."]
                        }})
            elif address:
                address.delete()
                instance.address = None

        try:
            res = super(PropertySerializer, self).update(instance, validated_data)
        except IntegrityError:
            raise serializers.ValidationError({'property': {
                'parid': ["Prperty with this parid already exists."]
            }})
        return res



class OwnerSerializer(serializers.ModelSerializer):

    addresses = NestedOwnerAddressSerializer(required=False, allow_null=True,
                                             many=True)

    class Meta:
        model = Owner
        fields = '__all__'

    @transaction.atomic()
    def create(self, validated_data):
        addresses_data = validated_data.pop('addresses', None) or []
        instance = super(OwnerSerializer, self).create(validated_data)
        for address_data in addresses_data:
            try:
                OwnerAddress.objects.create(owner=instance, **address_data)
            except IntegrityError:
                raise serializers.ValidationError({'address': {
                    'idhash': ["Address with this idhash already exists."]
                    }})

        return instance

    @transaction.atomic()
    def update(self, instance, validated_data):
        if 'addresses' in validated_data:
            addresses_data = validated_data.pop('addresses') or []
            addresses = instance.addresses.all()
            address_ids = {a.id: a for a in addresses}
            for address_data in addresses_data:
                address_id = address_data.pop('id', None)
                try:
                    if not address_id:
                        OwnerAddress.objects.create(owner=instance,
                                                    **address_data)
                    elif address_id in address_ids:
                        address = address_ids.pop(address_id)
                        for attr, value in address_data.items():
                            setattr(address, attr, value)
                        address.save()
                except IntegrityError:
                    raise serializers.ValidationError({'address': {
                        'idhash': ["Address with this idhash already exists."]
                        }})

            for address in address_ids.values():
                address.delete()

        return super(OwnerSerializer, self).update(instance, validated_data)


class AccountSerializer(serializers.ModelSerializer):
    class Meta:
        model = Account
        fields = '__all__'


class LienAuctionSerializer(serializers.ModelSerializer):
    class Meta:
        model = LienAuction
        fields = '__all__'


# ###################################################################################################
# !!! dont touch this section. we need this section to patch some serializers to inject some data !!!
# ###################################################################################################
def _perd(c):
    return inspect.isclass(c) and c.__module__ == _perd.__module__

classes = inspect.getmembers(sys.modules[__name__], _perd)
for class_name, klass in classes:
    if not issubclass(klass, serializers.ModelSerializer):
        continue
    meta = getattr(klass, 'Meta', None)
    if not meta:
        continue
    model = getattr(klass.Meta, 'model', None)
    if not model or (not issubclass(model, CountyBaseModel)):
        continue

    fields = getattr(klass.Meta, 'fields', None)
    if fields:
        if fields == '__all__':
            delattr(klass.Meta, 'fields')
            klass.Meta.exclude = ('county',)
    else:
        exclude = tuple(getattr(klass.Meta, 'exclude', None) or ())
        klass.Meta.exclude = exclude + ('county',)
