from rest_framework import serializers
from django.conf import settings
from rest_framework.exceptions import ValidationError

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


class OnlyIdSer(serializers.Serializer):

    id = serializers.IntegerField()


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


class QuestionSer(serializers.Serializer):

    id = serializers.IntegerField(read_only=True)
    type = serializers.IntegerField()
    typed_content = serializers.CharField()


class EventSer(serializers.Serializer):

    id = serializers.IntegerField(read_only=True)
    name = serializers.CharField()
    date_start = serializers.DateTimeField()
    date_end = serializers.DateTimeField()
    rules = serializers.CharField()
    process = serializers.CharField()
    groups = OnlyIdSer(many=True)
    questions = QuestionSer(many=True)

    def create(self, validated_data):

        participant = models.Participant.objects.get(user=validated_data['user'])

        if validated_data['date_start'] > validated_data['date_end']:
            raise ValidationError("Дата начала события не может быть раньше даты конца")

        group_ids = [it['id'] for it in validated_data['groups']]
        groups = models.Group.objects.filter(
            owner=participant, id__in=group_ids, event_lock=False)

        if groups.count() != len(group_ids):
            raise ValidationError("Не все группы доступны для создания события")

        event = models.Event.objects.create(
            name=validated_data['name'],
            date_start=validated_data['date_start'],
            date_end=validated_data['date_end'],
            rules=validated_data['rules'],
            process=validated_data['process'],
            owner=participant)

        event.groups = groups
        event.save()

        # Блокирование групп
        for group in groups:
            group.event_lock = True
            group.save()

        # Создание вопросов и добавление их к event
        for question in validated_data['questions']:
            models.Question.objects.create(
                event=event,
                type=question['type'],
                typed_content=question['typed_content'])

        return event
