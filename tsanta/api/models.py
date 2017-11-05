from django.contrib.auth.models import User
from django.db import models
from django.core.validators import validate_slug
from django.core import exceptions as django_exceptions


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
    phone = models.CharField(max_length=15)
    email = models.EmailField()
    social_network_link = models.CharField(max_length=200)
    age = models.SmallIntegerField()
    sex = models.SmallIntegerField(choices=SEX_CHOICES)

    def __str__(self):

        return 'Participant[{0}]: {1} {2}'.format(self.id, self.name, self.surname)

    def __repr__(self):

        return self.__str__()


class City(models.Model):

    _name = models.CharField(max_length=100)
    freq = models.IntegerField(default=0)

    @property
    def name(self):

        return self._name.capitalize()

    @classmethod
    def suggest(cls, text, limit=10):

        items = cls.objects.filter(_name__istartswith=text).order_by('-freq')

        if text != '':
            items = items[:limit]

        # Сделаем городишки с большой буквы
        for i, item in enumerate(items):
            items[i]._name = item._name.capitalize()

        return items

    def __str__(self):

        return 'City[{0}]: {1}'.format(self.id, self.name)

    def __repr__(self):

        return self.__str__()

    class Meta:

        verbose_name_plural = "Cities"


class Group(models.Model):

    short_name = models.CharField(max_length=500)
    alt_names = models.TextField()
    city = models.ForeignKey(City)
    slug = models.SlugField(unique=True)
    owner = models.ForeignKey(Participant)
    event_lock = models.BooleanField(default=False)
    tag = models.CharField(max_length=500, default="")

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

    def __str__(self):

        return 'Group[{0}]: {1}'.format(self.id, self.short_name)


class Question(models.Model):

    QUESTION_TYPES = (
        (0, "Text"),
        (1, "Radio")
    )

    type = models.SmallIntegerField(choices=QUESTION_TYPES, default=QUESTION_TYPES[0])
    json = models.TextField()

    def __str__(self):

        return 'Question[{0}]'.format(self.id)


class Event(models.Model):

    name = models.CharField(max_length=100)
    date_start = models.DateTimeField()
    date_end = models.DateTimeField()
    groups = models.ManyToManyField(Group)
    questions = models.ManyToManyField(Question)

    def __str__(self):

        return 'Event[{0}]: {1}'.format(self.id, self.name)


class Questionnaire(models.Model):

    participant = models.ForeignKey(Participant)
    event = models.ForeignKey(Event)
    ward = models.ForeignKey("self", null=True, blank=True)
    questions_answers = models.TextField(null=False, blank=True)
    group = models.ForeignKey(Group)
    is_closed = models.BooleanField(default=False)
    participation_confirmed = models.BooleanField(default=False)

    def __str__(self):

        return 'Questionnaire[{0}]: {1} {2}'.format(
            self.id, self.participant.name, self.participant.surname)


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
