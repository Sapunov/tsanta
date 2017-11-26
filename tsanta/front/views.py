from django.shortcuts import render, redirect
from api.models import Group, Participant

from tsanta import misc
from . import exceptions


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
        context['top_header_title'] = 'Not Found =('
        return render(request, "front/application.html", context=context)

    event = current_group.current_event

    if not event.in_progress:
        context['found'] = False
        context['notstarted'] = True
        context['top_header_title'] = 'В пути...'
        return render(request, "front/application.html", context=context)

    context['top_header_title'] = current_group.repr_name
    context['rules'] = event.rules_html
    context['process'] = event.process_html
    context['questions'] = event.questions.all()
    context['event_id'] = event.pk
    context['group_id'] = current_group.pk

    return render(request, "front/application.html", context=context)


def thanks(request):

    context = {
        'top_header_title': 'Благодарит'
    }

    return render(request, "front/thanks.html", context=context)


def confirm(request):

    context = {
        'message': '',
        'top_header_title': 'Подтверждает'
    }

    try:
        parts = request.path_info.lstrip('/').split('/')

        if len(parts) != 4:
            raise exceptions.ConfirmationError

        confirm_type = parts[1]
        try:
            identity = int(parts[2])
        except ValueError:
            raise exceptions.ConfirmationError
        content_hash = parts[3]

        if confirm_type == 'email':
            try:
                participant = Participant.objects.get(pk=identity)
            except Participant.DoesNotExist:
                raise exceptions.ConfirmationError

            if content_hash != participant.get_hash():
                raise exceptions.ConfirmationError

            if participant.email_confirmed:
                raise exceptions.ConfirmationError('Ваш email не нуждается в подтверждении')

            participant.email_confirmed = True
            participant.save()

            context['message'] = 'Спасибо! Ваш email подтвержден.'
            return render(request, "front/confirm.html", context=context)

        raise exceptions.ConfirmationError
    except exceptions.ConfirmationError as exc:
        context['message'] = str(exc)
        return render(request, "front/confirm.html", context=context)

