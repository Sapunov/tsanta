from django.shortcuts import render, redirect
from api.models import Group

from tsanta import misc


def index(request):

    context = {
        'app_version': misc.random_string(),
        'top_header_title': 'В здании'
    }

    return render(request, "front/index.html", context=context)


def application(request):

    context = {
        'app_version': misc.random_string(),
    }

    path = request.path_info.lstrip('/')

    try:
        current_group = Group.objects.get(event_lock=True, slug=path)
        context['found'] = True
    except Group.DoesNotExist:
        context['found'] = False
        return render(request, "front/application.html", context=context)

    event = current_group.current_event

    context['top_header_title'] = current_group.repr_name
    context['rules'] = event.rules_html
    context['process'] = event.process_html
    context['questions'] = event.questions.all()

    return render(request, "front/application.html", context=context)


def thanks(request):

    context = {}

    return render(request, "front/thanks.html", context=context)
