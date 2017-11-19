from rest_framework import serializers
from django.conf import settings
from rest_framework.exceptions import ValidationError
import mistune

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


class EventForGroupSer(serializers.Serializer):

    id = serializers.IntegerField()
    name = serializers.CharField()


class GroupSer(serializers.Serializer):

    id = serializers.IntegerField(read_only=True)
    short_name = serializers.CharField()
    alt_names = serializers.CharField(allow_blank=True, required=False)
    repr_name = serializers.CharField()
    city = CitySer()
    slug = serializers.SlugField()
    tag = serializers.CharField(default='')
    event_lock = serializers.BooleanField(read_only=True)
    current_event = EventForGroupSer(read_only=True, required=False)

    def create(self, validated_data):

        participant = models.Participant.objects.get(user=validated_data['user'])
        city = models.City.objects.get(pk=validated_data['city']['id'])

        group = models.Group.objects.create(
            short_name=validated_data['short_name'],
            alt_names=validated_data['alt_names'],
            repr_name=validated_data['repr_name'],
            city=city,
            slug=validated_data['slug'],
            owner=participant)

        return group

    def update(self, instance, validated_data):

        city = models.City.objects.get(pk=validated_data['city']['id'])

        instance.city = city
        instance.short_name = validated_data['short_name']
        instance.alt_names = validated_data['alt_names']
        instance.repr_name = validated_data['repr_name']
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

    id = serializers.IntegerField(required=False)
    type = serializers.IntegerField()
    typed_content = serializers.CharField()
    has_answers = serializers.BooleanField(required=False)


class EventSer(serializers.Serializer):

    id = serializers.IntegerField(read_only=True)
    name = serializers.CharField()
    date_start = serializers.DateTimeField()
    date_end = serializers.DateTimeField()
    rules = serializers.CharField()
    rules_html = serializers.CharField(read_only=True)
    process = serializers.CharField()
    process_html = serializers.CharField(read_only=True)
    groups = OnlyIdSer(many=True)
    questions = QuestionSer(many=True)

    def validate(self, data):

        if data['date_start'] > data['date_end']:
            raise ValidationError("Дата начала события не может быть раньше даты конца")

        if not data['groups']:
            raise ValidationError('Нельзя создать событие без групп')

        return data

    def create(self, validated_data):

        participant = models.Participant.objects.get(user=validated_data['user'])
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
            rules_html=mistune.markdown(validated_data['rules']),
            process=validated_data['process'],
            process_html=mistune.markdown(validated_data['process']),
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

    def update(self, instance, validated_data):

        participant = models.Participant.objects.get(user=validated_data['user'])

        requested_gids = [it['id'] for it in validated_data['groups']]
        bound_gids = [
            gid for gid in instance.groups.values_list('id', flat=True)
        ]

        # ID групп, которые необходимо разблокировать (удаленные из события группы)
        unbound_gids = [
            gid for gid in bound_gids if gid not in requested_gids
        ]

        # ID групп, которые необходимо заблокировать (добавленные к событию группы)
        new_gids = [
            gid for gid in requested_gids
            if gid not in unbound_gids and gid not in bound_gids
        ]

        # Можно ли разблокировать группы, которые просят удалить из события?
        unlocked_groups = models.Group.objects.filter(
            owner=participant, id__in=unbound_gids, event_lock=True
        )
        if unlocked_groups.count() != len(unbound_gids):
            raise ValidationError("Не все группы можно удалить из события")

        # Можно ли заблокировать группы, которые просят добавить?
        locked_groups = models.Group.objects.filter(
            owner=participant, id__in=new_gids, event_lock=False
        )
        if locked_groups.count() != len(new_gids):
            raise ValidationError("Не все группы можно добавить к событию")

        final_groups_ids = [
            gid for gid in requested_gids
            if gid not in unbound_gids
        ]

        groups = models.Group.objects.filter(
            owner=participant, id__in=final_groups_ids
        )

        instance.name = validated_data['name']
        instance.date_start = validated_data['date_start']
        instance.date_end = validated_data['date_end']
        instance.rules = validated_data['rules']
        instance.process = validated_data['process']
        instance.rules_html = mistune.markdown(validated_data['rules'])
        instance.process_html = mistune.markdown(validated_data['process'])

        # Блокирование групп
        for group in groups:
            group.event_lock = True
            group.save()

        # Разблокирование групп
        for group in unlocked_groups:
            group.event_lock = False
            group.save()

        instance.groups = groups
        instance.save()


        # Все вопросы запроса, имеющие id (по мнению клиента)
        questions_with_ids = {
            q['id']: q for q in validated_data['questions'] if 'id' in q
        }

        # Существующие вопросы события
        bound_question_ids = [
            qid for qid in instance.questions.values_list('id', flat=True)
        ]

        # Удаляем ненужные вопросы события
        unbound_question_ids = [
            qid for qid in bound_question_ids if qid not in questions_with_ids.keys()
        ]
        if unbound_question_ids:
            questions = models.Question.objects.filter(id__in=unbound_question_ids)
            invulnerable_questions = False
            for q in questions:
                invulnerable_questions = q.has_answers()
                if invulnerable_questions:
                    break
            
            if invulnerable_questions:
                raise ValidationError("Нельзя удалять вопросы, на которые уже есть ответы")
            else:
                questions.delete()

        # Проверяем оставшиеся вопросы на наличие изменений
        mod_questions_ids = [
            qid for qid in bound_question_ids if qid not in unbound_question_ids
        ]
        if mod_questions_ids:
            questions = models.Question.objects.filter(id__in=mod_questions_ids)
            for q in questions:
                if not q.has_answers() \
                   and q.typed_content != questions_with_ids[q.id]['typed_content']:
                    q.typed_content = questions_with_ids[q.id]['typed_content']
                    q.save()
                # TODO Type

        # Абсолютно новые вопросы
        new_questions = [
            q for q in validated_data['questions'] if not 'id' in q
        ]

        for question in new_questions:
            models.Question.objects.create(
                event=instance,
                type=question['type'],
                typed_content=question['typed_content'])

        return instance
