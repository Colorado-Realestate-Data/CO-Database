from rest_framework import serializers
from django.db import IntegrityError, transaction

from prop.models import Property, Owner, PropertyAddress, OwnerAddress


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
        instance = super(PropertySerializer, self).create(validated_data)
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

        return super(PropertySerializer, self).update(instance, validated_data)


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
