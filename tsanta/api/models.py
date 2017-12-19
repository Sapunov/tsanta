from datetime import timedelta
from random import shuffle
import logging
import os

from django.conf import settings
from django.contrib.auth.models import User
from django.core import exceptions as django_exceptions
from django.core.validators import validate_slug
from django.db import models
from django.db.models import Q, Count
from django.utils import timezone
from jinja2 import Template

from . import mailgun, exceptions
from tsanta import misc


log = logging.getLogger('main.' + __name__)


class IsExists:

    def __init__(self, is_exists):

        self.is_exists = is_exists


class CheckSlug:

    def __init__(self, is_exists, is_correct):

        self.is_exists = is_exists
        self.is_correct = is_correct
        self.is_ok = (not self.is_exists) & self.is_correct


class Participant(models.Model):

    SEX_CHOICES = (
        (0, "Мужчина"),
        (1, "Женщина"),
        (2, "Не определено")
    )

    user = models.OneToOneField(User)
    name = models.CharField(max_length=50)
    surname = models.CharField(max_length=50)
    phone = models.CharField(max_length=15, null=True, blank=True)
    email = models.EmailField(unique=True)
    social_network_link = models.URLField(null=True, blank=True)
    sex = models.SmallIntegerField(choices=SEX_CHOICES, default=2)
    email_confirmed = models.BooleanField(default=False)

    @classmethod
    def exists(cls, user):

        try:
            cls.objects.get(user=user)
        except cls.DoesNotExist:
            return False

        return True

    @classmethod
    def email_exists(cls, email):

        try:
            cls.objects.get(email=email)
        except cls.DoesNotExist:
            return False

        return True

    @classmethod
    def get_name_surname(cls, user):

        participant = cls.objects.get(user=user)

        return '{name} {surname}'.format(
            name=participant.name.capitalize(),
            surname=participant.surname.capitalize())

    def get_hash(self):

        return misc.sha1_hash(settings.SECRET_KEY + self.email + str(self.pk) + str(self.user.pk))

    def confirm_email(self):

        self.email_confirmed = True
        self.save()

        from api.models import Questionnaire
        questionnaires = Questionnaire.objects.filter(
            participant=self, state=1, is_closed=False)

        for questionnaire in questionnaires:
            questionnaire.state = 2
            questionnaire.save()

    def __str__(self):

        return 'Participant[{0}]: {1} {2}; {3}'.format(self.id, self.name, self.surname, self.email)

    def __repr__(self):

        return self.__str__()


class City(models.Model):

    name = models.CharField(max_length=100)
    freq = models.IntegerField(default=0)

    @classmethod
    def suggest(cls, text, limit=10):

        items = cls.objects.filter(name__istartswith=text).order_by('-freq')

        if limit and limit > 0:
            items = items[:limit]

        return items

    @classmethod
    def update_frequencies(cls):

        from api.models import Group
        groups = Group.objects.all()

        cities_map = {}
        for group in groups:
            if not group.city.pk in cities_map:
                cities_map[group.city.pk] = 0
            cities_map[group.city.pk] += 1

        cities = cls.objects.all()

        for city in cities:
            if city.pk in cities_map:
                city.freq = cities_map[city.pk]
                city.save()

    def __str__(self):

        return 'City[{0}]: {1}'.format(self.id, self.name)

    def __repr__(self):

        return self.__str__()

    class Meta:

        verbose_name_plural = "Cities"


class EventStatistics:

    count_groups = 0
    count_participants = 0
    count_cities = 0
    group_dist = []
    city_dist = []
    overall_participants = 0

    def __init__(self, participants):

        self.count_participants = len(participants)

        group_dist_tmp = {}
        city_dist_tmp = {}

        for participant in participants:
            self.overall_participants += 1

            if not participant.group.id in group_dist_tmp:
                group_dist_tmp[participant.group.id] = {
                    'id': participant.group.id,
                    'name': participant.group.short_name,
                    'count': 1
                }
            else:
                group_dist_tmp[participant.group.id]['count'] += 1

            if not participant.group.city.id in city_dist_tmp:
                city_dist_tmp[participant.group.city.id] = {
                    'id': participant.group.city.id,
                    'name': participant.group.city.name,
                    'count': 1
                }
            else:
                city_dist_tmp[participant.group.city.id]['count'] += 1

        self.count_cities = len(city_dist_tmp.keys())
        self.count_groups = len(group_dist_tmp.keys())

        self.group_dist = sorted(group_dist_tmp.values(), key=lambda it: it['count'], reverse=True)
        self.city_dist = sorted(city_dist_tmp.values(), key=lambda it: it['count'], reverse=True)


class Event(models.Model):

    name = models.CharField(max_length=100)
    date_start = models.DateTimeField()
    date_end = models.DateTimeField()
    groups = models.ManyToManyField("Group")
    rules = models.TextField()
    rules_html = models.TextField()
    process = models.TextField()
    process_html = models.TextField()
    owner = models.ForeignKey(Participant)

    @classmethod
    def get_my_events(cls, user, event_id=None, prefix=''):

        participant = Participant.objects.get(user=user)

        items = cls.objects.filter(owner=participant, name__istartswith=prefix)

        if not event_id is None:
            items = items.filter(pk=event_id)

            if items.count() == 1:
                return items[0]
            else:
                return None

        return items

    @property
    def in_progress(self):

        return self.date_end >= timezone.now() and self.date_start <= timezone.now()

    def event_statistics(self):

        from api.models import Questionnaire
        questionnaires = Questionnaire.objects.filter(event=self)

        return EventStatistics(questionnaires)

    def send_confirms(self):

        from api.models import Questionnaire
        questionnaires = Questionnaire.objects.filter(event=self, state=2)

        from api.models import Notification
        for questionnaire in questionnaires:
            Notification.objects.create(
                type=1,
                name='Подтверждение участия',
                questionnaire=questionnaire)

    def assign_wards(self, type_):

        # Allowed types: city, group, all

        from api.models import Questionnaire
        questionnaires = Questionnaire.objects.filter(
            event=self, is_closed=False, participation_confirmed=True)

        # TODO: нельзя трогать тех, кто уже является чьи-то
        # подопечным, а этот кто-то уже is_closed=True

        temp = {}

        if type_ == 'city':
            for questionnaire in questionnaires:
                city_pk = questionnaire.group.city.pk

                if not city_pk in temp:
                    temp[city_pk] = []

                temp[city_pk].append(questionnaire.pk)
        elif type_ == 'group':
            for questionnaire in questionnaires:
                group_pk = questionnaire.group.pk

                if not group_pk in temp:
                    temp[group_pk] = []

                temp[group_pk].append(questionnaire.pk)
        elif type_ == 'all':
            temp[0] = []

            for questionnaire in questionnaires:
                temp[0].append(questionnaire.pk)
        else:
            raise ValueError('Not allowed assign type: {0}'.format(type_))

        temp = list(temp.values())
        assign_map = {}

        for i, _ in enumerate(temp):
            shuffle(temp[i])

            temp_len = len(temp[i])

            if temp_len > 1:
                for j in range(temp_len):
                    assign_map[temp[i][j]] = temp[i][(j + 1) % temp_len]
            else:
                # TODO: сделать обработку одиночек
                pass

        for key, value in assign_map.items():
            if key != value:
                questionnaire = Questionnaire.objects.get(pk=key)
                ward = Questionnaire.objects.get(pk=value)

                questionnaire.ward = ward
                questionnaire.save()

    def __str__(self):

        return 'Event[{0}]: {1}'.format(self.id, self.name)


class Group(models.Model):

    short_name = models.CharField(max_length=500)
    alt_names = models.TextField()
    repr_name = models.CharField(max_length=503)
    city = models.ForeignKey(City)
    slug = models.SlugField(unique=True)
    owner = models.ForeignKey(Participant)
    event_lock = models.BooleanField(default=False)
    locked_by = models.ForeignKey(Event, null=True, blank=True)
    searchable = models.BooleanField(default=True)

    @classmethod
    def get_my_groups(cls, user, prefix="", limit=20):

        query = prefix.lower()
        query_kb_inverse = misc.keyboard_layout_inverse(query)

        participant = Participant.objects.get(user=user)

        groups = cls.objects.filter(
            Q(owner=participant) & (
                # С нормальный раскладкой
                Q(short_name__icontains=query)
                | Q(alt_names__icontains=query)
                | Q(slug__icontains=query)
                # С инвертированной раскладкой
                | Q(short_name__icontains=query_kb_inverse)
                | Q(alt_names__icontains=query_kb_inverse)
            ))

        registered = {}

        # Сбор статистики по зарегистрировавшимся людям в группах
        if groups.count() > 0:
            for item in Questionnaire.objects.filter(
                    is_closed=False).values('group').annotate(count=Count('group')):
                registered[item['group']] = item['count']

        answer = []

        for group in groups:
            in_short_name = group.short_name.lower().count(query)
            in_alt_names = group.alt_names.lower().count(query)
            count_participants = 0
            startswith = 1 if group.short_name.lower().startswith(query) else 0

            if group.id in registered:
                count_participants = registered[group.id]

            # Супер формула
            score = (in_short_name / len(group.short_name)) * 0.3
            score += startswith * 0.4
            if group.alt_names:
                score += (in_alt_names / len(group.alt_names)) * 0.2
            score += count_participants * 0.1

            answer.append(
                {'group': group,
                 'score': score})

        if answer:
            answer.sort(key=lambda it: it['score'], reverse=True)

        return [it['group'] for it in answer[:limit]]

        return groups

    @classmethod
    def check_slug(cls, text):

        text = text.lower()

        is_exists = cls.objects.filter(slug=text).count() > 0
        is_exists = is_exists or text in settings.RESERVED_SLUG_WORDS

        is_correct = True

        try:
            validate_slug(text)
        except django_exceptions.ValidationError:
            is_correct = False

        return CheckSlug(is_exists, is_correct)

    @property
    def current_event(self):

        if not self.event_lock:
            return None

        return self.locked_by

    @classmethod
    def suggest(cls, query, limit=5):

        query = query.lower()
        query_kb_inverse = misc.keyboard_layout_inverse(query)

        if len(query) > 1:
            groups = cls.objects.filter(
                Q(searchable=True) & Q(event_lock=True) & (
                    # С нормальный раскладкой
                    Q(short_name__icontains=query)
                    | Q(alt_names__icontains=query)
                    | Q(slug__icontains=query)
                    # С инвертированной раскладкой
                    | Q(short_name__icontains=query_kb_inverse)
                    | Q(alt_names__icontains=query_kb_inverse)
                ))
        else:
            groups = cls.objects.filter(
                Q(searchable=True) & Q(event_lock=True) & (
                    # С нормальный раскладкой
                    Q(short_name__icontains=query)
                    | Q(alt_names__icontains=query)
                    | Q(slug__icontains=query)
                ))

        registered = {}

        # Сбор статистики по зарегистрировавшимся людям в группах
        if groups.count() > 0:
            for item in Questionnaire.objects.filter(
                    is_closed=False).values('group').annotate(count=Count('group')):
                registered[item['group']] = item['count']

        answer = []

        for group in groups:
            in_short_name = group.short_name.lower().count(query)
            in_alt_names = group.alt_names.lower().count(query)
            count_participants = 0
            startswith = 1 if group.short_name.lower().startswith(query) else 0

            if group.id in registered:
                count_participants = registered[group.id]

            # Супер формула
            score = (in_short_name / len(group.short_name)) * 0.3
            score += startswith * 0.4
            if group.alt_names:
                score += (in_alt_names / len(group.alt_names)) * 0.2
            score += count_participants * 0.1

            answer.append(
                {'short_name': group.short_name,
                 'slug': group.slug,
                 'score': score})

        if answer:
            answer.sort(key=lambda it: it['score'], reverse=True)

        return answer[:limit]


    def __str__(self):

        return 'Group[{0}]: {1}'.format(self.id, self.short_name)


class CountItem():

    def __init__(self, state, count=0):

        self.state = state
        self.count = count


class ParticipantsAns:

    def __init__(self, q, questionnaires, state_counters):

        self.q = q
        self.questionnaires = questionnaires
        self.state_counters = state_counters


class Questionnaire(models.Model):

    STATES = (
        (0, 'Registered'),
        (1, 'EmailConfirmationSent'),
        (2, 'EmailConfirmed'),
        (3, 'ConfirmationSent'),  # О подтвержнее участия
        (4, 'Confirmed'),         #
        (5, 'WardAssigned'),
        (6, 'WardSent')
    )

    participant = models.ForeignKey(Participant)
    event = models.ForeignKey(Event)
    ward = models.ForeignKey("self", null=True, blank=True)
    group = models.ForeignKey(Group)
    is_closed = models.BooleanField(default=False)
    participation_confirmed = models.BooleanField(default=False)
    state = models.SmallIntegerField(choices=STATES, default=0)

    def get_hash(self):

        return misc.sha1_hash(settings.SECRET_KEY \
            + str(self.participant.pk) \
            + str(self.event.pk) \
            + str(self.group.pk))

    def confirm_participation(self):

        self.state = 4
        self.save()

    @classmethod
    def get_event_questionnaires(cls, event, count=20, filter_text=None, filter_state=-1):

        participants_ids = []

        states = {}
        for questionnaire in cls.objects.filter(event=event):
            if not questionnaire.state in states:
                states[questionnaire.state] = CountItem(state=questionnaire.state)
            states[questionnaire.state].count += 1

        if filter_text:
            filter_text = filter_text.lower()

            participants = Participant.objects.filter(
                Q(name__icontains=filter_text)
                | Q(surname__icontains=filter_text)
                | Q(phone__icontains=filter_text)
                | Q(email__icontains=filter_text)
            )

            participants_ids = [it.id for it in participants]

            if filter_state >= 0:
                questionnaires = cls.objects.filter(
                    event=event, participant__in=participants_ids, state=filter_state)
            else:
                questionnaires = cls.objects.filter(
                    event=event, participant__in=participants_ids)
        else:
            if filter_state >= 0:
                questionnaires = cls.objects.filter(event=event, state=filter_state)
            else:
                questionnaires = cls.objects.filter(event=event)

        return ParticipantsAns(
            filter_text,
            questionnaires[:count],
            sorted(states.values(), key=lambda it: it.state))

    def __str__(self):

        return 'Questionnaire[{0}]: {1} {2}'.format(
            self.id, self.participant.name, self.participant.surname)


class Question(models.Model):

    QUESTION_TYPES = (
        (0, "Text"),
        (1, "Radio")
    )

    event = models.ForeignKey(Event, related_name="questions")
    type = models.SmallIntegerField(choices=QUESTION_TYPES, default=QUESTION_TYPES[0])
    typed_content = models.TextField()

    def has_answers(self):

        return self.answer_set.count() > settings.QUESTION_DELETE_TRESHOLD

    def __str__(self):

        return 'Question[{0}]'.format(self.id)


class Answer(models.Model):

    question = models.ForeignKey(Question)
    questionnaire = models.ForeignKey(Questionnaire)
    content = models.TextField()

    def __str__(self):

        return 'Answer[{0}]'.format(self.id)

    def __repr__(self):

        return self.__str__()


class KVParams(models.Model):

    TYPES = (
        (0, 'text'),
        (1, 'datetime')
    )

    key = models.CharField(max_length=100, primary_key=True)
    value = models.TextField()
    type = models.SmallIntegerField(choices=TYPES, default=0)

    @classmethod
    def get(cls, key):

        key = key.lower().strip()

        try:
            obj = cls.objects.get(pk=key)
        except cls.DoesNotExist:
            return None

        if obj.type == 1:
            obj.value = timezone.datetime.strptime(
                obj.value, settings.KV_DATETIME_FORMAT)

        return obj

    @classmethod
    def set(cls, key, value, type_=0, update=False):

        key = key.lower().strip()

        if not type_ in [it[0] for it in cls.TYPES]:
            raise exceptions.UnsupportedKeyType

        obj = cls.get(key)

        if type_ == 0:
            if obj is None:
                obj = cls.objects.create(pk=key, value=value)
            elif update:
                obj.value = value
                obj.type = type_
                obj.save()
            else:
                raise exceptions.KeyExistsException
        elif type_ == 1:
            if not isinstance(value, timezone.datetime):
                raise ValueError('Value is not datetime. Change type_ param')

            value = value.strftime(settings.KV_DATETIME_FORMAT)

            if obj is None:
                obj = cls.objects.create(key=key, value=value, type=type_)
            elif update:
                obj.value = value
                obj.type = type_
                obj.save()
            else:
                raise exceptions.KeyExistsException

            # Чтобы в value было datetime, сделаем так:
            return cls.get(key)

        return obj

    @classmethod
    def set_update(cls, key, value, type_=0):

        return cls.set(key, value, type_, update=True)

    def __str__(self):

        return 'KVParam[{0}]: {1}'.format(self.pk, self.value)

    def __repr__(self):

        return self.__str__()


class Notification(models.Model):

    TYPE = (
        (0, 'Email confirmation'),
        (1, 'Participation confirmation'),
        (2, 'Send ward')
    )

    STATES = (
        (0, 'Created'),
        (1, 'Rejected'),
        (2, 'Accepted'),
        (3, 'TemporaryFailed'),
        (4, 'FailedPermanently'),
        (5, 'Delivered'),
        (6, 'Opened')
    )

    name = models.CharField(max_length=100)
    type = models.SmallIntegerField(choices=TYPE)
    questionnaire = models.ForeignKey(Questionnaire)
    date_created = models.DateTimeField(auto_now_add=True)
    state = models.SmallIntegerField(choices=STATES, default=0)
    provider_mail_id = models.CharField(null=True, blank=True, max_length=200)

    def send_email_confirmation(self):

        if self.type != 0:
            raise ValueError('This is wrong method for this notification type')

        subject = 'Подтверждение email'

        template_file = os.path.join(
            settings.EMAILS_TEMPLATES_DIR, 'email_confirmation.html')

        template = None

        with open(template_file, 'r') as opened:
            text = opened.read()
            template = Template(text)

        html = template.render(
            participant_id=self.questionnaire.participant.pk,
            confirm_hash=self.questionnaire.participant.get_hash())

        provider_answer = mailgun.send_html(
            settings.MAIL_FROM,
            self.questionnaire.participant.email,
            subject,
            html,
            settings.MAIL_REPLY_TO,
            ['email_confirmation'])

        if provider_answer:
            self.state = 2
            self.provider_mail_id = provider_answer
            self.questionnaire.state = 1
            self.questionnaire.save()
        else:
            self.state = 1

        self.save()

    def send_participation_confirmation(self):

        if self.type != 1:
            raise ValueError('This is wrong method for this notification type')

        subject = 'Подтверждение участия в Тайном Санте!'

        template_file = os.path.join(
            settings.EMAILS_TEMPLATES_DIR, 'participation_confirm.html')

        template = None

        with open(template_file, 'r') as opened:
            text = opened.read()
            template = Template(text)

        html = template.render(
            questionnaire_id=self.questionnaire.pk,
            confirm_hash=self.questionnaire.get_hash())

        provider_answer = mailgun.send_html(
            settings.MAIL_FROM,
            self.questionnaire.participant.email,
            subject,
            html,
            settings.MAIL_REPLY_TO,
            ['participation_confirmation'])

        if provider_answer:
            self.state = 2
            self.provider_mail_id = provider_answer
            self.questionnaire.state = 3
            self.questionnaire.save()
        else:
            self.state = 1

        self.save()

    def send_ward(self):

        if self.type != 2:
            raise ValueError('This is wrong method for this notification type')

        subject = 'Ваш подопечный'

        ward = self.questionnaire.ward

        name = ward.participant.name
        surname = ward.participant.surname
        phone = ward.participant.phone
        social_network_link = ward.participant.social_network_link

        answers = []
        for ans in Answer.objects.filter(questionnaire=ward):
            answers.append({
                'question': ans.question.typed_content,
                'answer': ans.content
            })

        template_file = os.path.join(
            settings.EMAILS_TEMPLATES_DIR, 'ward.html')

        template = None

        with open(template_file, 'r') as opened:
            text = opened.read()
            template = Template(text)

        html = template.render(
            name=name,
            surname=surname,
            phone=phone,
            social_network_link=social_network_link,
            answers=answers
        )

        provider_answer = mailgun.send_html(
            settings.MAIL_FROM,
            self.questionnaire.participant.email,
            subject,
            html,
            settings.MAIL_REPLY_TO,
            ['ward'])

        if provider_answer:
            self.state = 2
            self.provider_mail_id = provider_answer
            self.questionnaire.is_closed = True
            self.questionnaire.save()
        else:
            self.state = 1

        self.save()

    @classmethod
    def send_queued(cls):

        for notification in cls.objects.all():
            if notification.state == 0 or notification.state == 1:
                if notification.type == 0:
                    notification.send_email_confirmation()
                elif notification.type == 1:
                    notification.send_participation_confirmation()
                elif notification.type == 2:
                    notification.send_ward()

    @classmethod
    def update_states(cls):

        utc_begin = KVParams.get('notification_utc_last')
        if utc_begin is None:
            utc_begin = timezone.now() - timedelta(days=366)
        else:
            utc_begin = utc_begin.value

        utc_end = timezone.now()

        items = mailgun.get_all_results(utc_begin, utc_end)

        log.info('There is %s events received from provider', len(items))

        messages_processed = set()

        for item in items:
            try:
                message_id = item['message']['headers']['message-id']
            except KeyError:
                continue

            # Так как события выбираются в обратном порядке,
            # то логично обрабатывать только самое последнее событи
            # для одного сообщения
            if message_id in messages_processed:
                continue

            try:
                notification = cls.objects.get(provider_mail_id=message_id)
            except cls.DoesNotExist:
                continue

            old_state = notification.state

            if item['event'] == 'accepted':
                notification.state = 2
            elif item['event'] == 'delivered':
                notification.state = 5
            elif item['event'] == 'failed':
                if item['severity'] == 'temporary':
                    notification.state = 3
                elif item['severity'] == 'permanent':
                    notification.state = 4
            # Ниже одинаковые статусы так как любой и данных статусов
            # провайдера означает открытое письмо, а открытие - финишный
            # статус нотификации
            elif item['event'] == 'opened':
                notification.state = 6
            elif item['event'] == 'clicked':
                notification.state = 6
            elif item['event'] == 'complained':
                notification.state = 6
            else:
                continue

            if notification.state > old_state:
                notification.save()

            messages_processed.add(message_id)

            log.info('%s exposed to a %s status', notification, notification.state)

        KVParams.set_update('notification_utc_last', utc_end, type_=1)

    def __str__(self):

        return 'Notification[{0}]: {1} to {2}'.format(
            self.id, self.name,
            self.questionnaire.participant)
