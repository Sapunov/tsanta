from rest_framework import serializers

from api import models


def deserialize(serializer_class, data):

    serializer = serializer_class(data=data)
    serializer.is_valid(raise_exception=True)

    return serializer


def serialize(serializer_class, instance, data=None, **kwargs):

    if data is None:
        serializer = serializer_class(instance, **kwargs)
    else:
        serializer = serializer_class(instance, data=data, **kwargs)
        serializer.is_valid(raise_exception=True)

    return serializer


class OnlyQSerReq(serializers.Serializer):

    q = serializers.CharField(allow_blank=True)


class OnlyQSer(serializers.Serializer):

    q = serializers.CharField(allow_blank=True, required=False, default='')


class CitySer(serializers.Serializer):

    id = serializers.IntegerField()
    name = serializers.CharField()


class GroupSer(serializers.Serializer):

    id = serializers.IntegerField(read_only=True)
    short_name = serializers.CharField()
    alt_names = serializers.CharField(allow_blank=True, required=False)
    city = CitySer()
    slug = serializers.SlugField()
    tag = serializers.CharField(default='')
    event_lock = serializers.BooleanField(read_only=True)

    def create(self, validated_data):

        participant = models.Participant.objects.get(user=validated_data['user'])
        city = models.City.objects.get(pk=validated_data['city']['id'])

        group = models.Group.objects.create(
            short_name=validated_data['short_name'],
            alt_names=validated_data['alt_names'],
            city=city,
            slug=validated_data['slug'],
            owner=participant)

        return group

    def update(self, instance, validated_data):

        city = models.City.objects.get(pk=validated_data['city']['id'])

        instance.city = city
        instance.short_name = validated_data['short_name']
        instance.alt_names = validated_data['alt_names']
        instance.slug = validated_data['slug']

        instance.save()

        return instance


class ExistsSer(serializers.Serializer):

    is_exists = serializers.BooleanField()


class CheckSlug(serializers.Serializer):

    is_exists = serializers.BooleanField()
    is_correct = serializers.BooleanField()
    is_ok = serializers.BooleanField()
