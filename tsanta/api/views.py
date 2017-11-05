from rest_framework.decorators import api_view, permission_classes
from rest_framework.exceptions import ValidationError
from rest_framework.response import Response
from rest_framework.views import APIView

from api import serializers
from api.models import City, Group
from api.serializers import serialize, deserialize


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


class GroupView(APIView):

    def get(self, request, group_id=None):

        if group_id is None:

            req_serializer = deserialize(serializers.OnlyQSer, request.query_params)

            items = Group.get_my_groups(request.user, prefix=req_serializer.data['q'])
            ans_serializer = serialize(serializers.GroupSer, items, many=True)
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
        serializer = serialize(serializers.GroupSer, group, data=request.data)

        serializer.save()

        return Response(serializer.data)


    def delete(self, request, group_id):

        group = Group.objects.get(pk=group_id)

        if group.event_lock:
            raise ValidationError('Нельзя удалить группу, пока она участвует в событии')

        group.delete()

        return Response()
