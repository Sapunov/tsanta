from django.contrib.auth.models import User
from django.db import models
from django.core.validators import validate_slug
from django.core import exceptions as django_exceptions
from django.utils import timezone
from django.db.models import Q, Count

from tsanta import misc

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
    email = models.EmailField()
    social_network_link = models.URLField(null=True, blank=True)
    age = models.SmallIntegerField(null=True, blank=True)
    sex = models.SmallIntegerField(choices=SEX_CHOICES, default=2)

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

    def __str__(self):

        return 'Participant[{0}]: {1} {2}'.format(self.id, self.name, self.surname)

    def __repr__(self):

        return self.__str__()


class City(models.Model):

    name = models.CharField(max_length=100)
    freq = models.IntegerField(default=0)

    @classmethod
    def suggest(cls, text, limit=10):

        items = cls.objects.filter(name__istartswith=text).order_by('-freq')

        if text != '':
            items = items[:limit]

        return items

    def __str__(self):

        return 'City[{0}]: {1}'.format(self.id, self.name)

    def __repr__(self):

        return self.__str__()

    class Meta:

        verbose_name_plural = "Cities"


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
    tag = models.CharField(max_length=500, default="", blank=True)

    @classmethod
    def get_my_groups(cls, user, prefix=""):

        participant = Participant.objects.get(user=user)

        items = cls.objects.filter(owner=participant, short_name__istartswith=prefix)

        return items

    @classmethod
    def check_slug(cls, text):

        text = text.lower()

        is_exists = cls.objects.filter(slug=text).count() > 0
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

        event = Event.objects.get(
            groups__id=self.id,
            date_start__lte=timezone.now(),
            date_end__gte=timezone.now())

        return event

    @classmethod
    def suggest(cls, query, limit=5):

        query = query.lower()
        query_kb_inverse = misc.keyboard_layout_inverse(query)

        groups = cls.objects.filter(
            Q(event_lock=True) & (
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


class Questionnaire(models.Model):

    participant = models.ForeignKey(Participant)
    event = models.ForeignKey(Event)
    ward = models.ForeignKey("self", null=True, blank=True)
    group = models.ForeignKey(Group)
    is_closed = models.BooleanField(default=False)
    participation_confirmed = models.BooleanField(default=False)

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

    def __str__(self):

        return 'Question[{0}]'.format(self.id)


class Answer(models.Model):

    question = models.ForeignKey(Question)
    questionnaire = models.ForeignKey(Questionnaire)
    content = models.TextField()


class Notification(models.Model):

    name = models.CharField(max_length=100)
    event = models.ForeignKey(Event)
    questionnaire = models.ForeignKey(Questionnaire)
    date_created = models.DateTimeField(auto_now_add=True)
    date_sended = models.DateTimeField(null=True)
    date_delivered = models.DateTimeField(null=True)
    date_opened = models.DateTimeField(null=True)

    def __str__(self):

        return 'Notification[{0}]: {1} to {2} {3}'.format(
            self.id, self.name,
            self.questionnaire.participant.name,
            self.questionnaire.participant.surname)
