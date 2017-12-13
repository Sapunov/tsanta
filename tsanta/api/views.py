from rest_framework.decorators import api_view, permission_classes
from rest_framework.exceptions import ValidationError, PermissionDenied, NotFound
from rest_framework.response import Response
from rest_framework.views import APIView
from rest_framework import status
from rest_framework.authentication import SessionAuthentication, BasicAuthentication

from api import serializers, exceptions
from api.models import City, Group, Event, Questionnaire
from api.serializers import serialize, deserialize
from django.conf import settings


class CityView(APIView):

    def get(self, request):

        req_serializer = deserialize(serializers.OnlyQSerReq, request.query_params)

        items = City.suggest(req_serializer.data['q'])

        ans_serializer = serialize(serializers.CitySer, items, many=True)

        return Response(ans_serializer.data)


@api_view()
@permission_classes([])
def check_slug(request):
    # Данный метод выполняется для неавторизованного пользователя

    req_serializer = deserialize(serializers.OnlyQSerReq, request.query_params)

    ans = Group.check_slug(req_serializer.data['q'])

    ans_serializer = serialize(serializers.CheckSlug, ans)

    return Response(ans_serializer.data)


@api_view()
@permission_classes([])
def suggest_group(request):
    '''Данный метод должен быть быстрым, поэтому тут не используется
       дополнительная сериализация после получения ответа'''

    req_serializer = deserialize(serializers.OnlyQSerReq, request.query_params)

    return Response(Group.suggest(req_serializer.data['q']))


class GroupAns:

    def __init__(self, q, groups):

        self.q = q
        self.groups = groups


class GroupView(APIView):

    def get(self, request, group_id=None):

        if group_id is None:
            req_serializer = deserialize(serializers.OnlyQSer, request.query_params)

            groups = Group.get_my_groups(request.user, prefix=req_serializer.data['q'])
            ans_serializer = serialize(
                serializers.GroupAnsSer,
                GroupAns(req_serializer.data['q'], groups))
        else:
            item = Group.objects.get(pk=group_id)
            ans_serializer = serialize(serializers.GroupSer, item)

        return Response(ans_serializer.data)

    def post(self, request, group_id=None):

        serializer = deserialize(serializers.GroupSer, data=request.data)
        serializer.save(user=request.user)

        return Response(serializer.data)

    def put(self, request, group_id):

        group = Group.objects.get(pk=group_id)

        # Группу может изменить только владелец
        if group.owner.user != request.user:
            raise PermissionDenied

        serializer = serialize(serializers.GroupSer, group, data=request.data)

        serializer.save()

        return Response(serializer.data)


    def delete(self, request, group_id):

        group = Group.objects.get(pk=group_id)

        # Группу может удалить только владелец
        if group.owner.user != request.user:
            raise PermissionDenied

        if group.event_lock:
            raise ValidationError('Нельзя удалить группу, пока она участвует в событии')

        group.delete()

        return Response()


class EventView(APIView):

    def get(self, request, event_id=None):

        if event_id is None:
            req_serializer = deserialize(serializers.OnlyQSer, request.query_params)
            events = Event.get_my_events(request.user, prefix=req_serializer.data['q'])
            ans_serializer = serialize(serializers.EventSer, events, many=True)
        else:
            event = Event.get_my_events(request.user, event_id=event_id)

            if event is None:
                raise NotFound

            ans_serializer = serialize(serializers.EventSer, event)

        return Response(ans_serializer.data)

    def post(self, request, event_id=None):

        serializer = deserialize(serializers.EventSer, data=request.data)
        serializer.save(user=request.user)

        return Response(serializer.data)


    def put(self, request, event_id):

        event = Event.objects.get(pk=event_id)

        # Событие может изменить только владелец
        if event.owner.user != request.user:
            raise PermissionDenied

        serializer = serialize(serializers.EventSer, event, data=request.data)
        serializer.save(user=request.user)

        return Response(serializer.data)


@api_view(['POST'])
@permission_classes([])
def submit_questionnaire(request):

    try:
        serializer = deserialize(serializers.SubmitFormSer, request.data)
        serializer.save()
    except exceptions.AlreadySignedException:
        return Response(
            status=status.HTTP_409_CONFLICT,
            data={"error": "Вы уже зарегистрированы на данной событие в этой группе"})

    return Response(status=status.HTTP_201_CREATED)


class ParticipantsAns:

    def __init__(self, q, questionnaires):

        self.q = q
        self.questionnaires = questionnaires


@api_view(['GET'])
def event_participants(request, event_id):

    event = Event.get_my_events(request.user, event_id=event_id)

    if event is None:
        raise NotFound

    req_serializer = deserialize(serializers.OnlyQSer, request.query_params)
    filter_text = req_serializer.data['q']

    questionnaires = Questionnaire.get_event_questionnaires(
        event, filter_text=filter_text)

    ans_serializer = serialize(
        serializers.QuestionnaireAnsSer,
        ParticipantsAns(filter_text, questionnaires))

    return Response(ans_serializer.data)


@api_view(['GET'])
def event_stat(request, event_id):

    event = Event.get_my_events(request.user, event_id=event_id)

    if event is None:
        raise NotFound

    stat = event.event_statistics()

    ans_serializer = serialize(serializers.EventStatSer, stat)

    return Response(ans_serializer.data)


@api_view(['POST'])
def assign_wards(request, event_id):

    req_serializer = deserialize(serializers.TypeFieldReq, request.query_params)
    type_ = req_serializer.data['type']

    if not type_ in settings.WARD_ASSIGN_TYPES:
        raise ValidationError('Переданный тип распределения не поддерживается')

    event = Event.get_my_events(request.user, event_id=event_id)

    if event is None:
        raise NotFound

    event.assign_wards(type_=type_)

    return Response(status=status.HTTP_200_OK)
