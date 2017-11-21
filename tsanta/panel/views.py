from django.shortcuts import render, redirect
from django.conf import settings

from django.contrib.auth.decorators import login_required
from django.contrib.auth import login, logout, authenticate
from django.contrib.auth.models import User

from api.models import Participant

from tsanta import misc


@login_required
def index_view(request):

    name_surname = None

    try:
        name_surname = Participant.get_name_surname(request.user)
    except Participant.DoesNotExist:
        logout_view(request)

    context = {
        # 'app_version': settings.APP_VERSION
        'app_version': misc.random_string(),
        'name_surname': name_surname
    }

    return render(request, 'panel/index.html', context)


def logout_view(request):

    logout(request)

    return redirect(settings.LOGIN_URL)


def login_view(request):

    context = {
        'loginpage': settings.LOGIN_URL,
        'error_message': None,
        'app_version': settings.APP_VERSION,
        'data': {}
    }

    next_url = request.GET.get('next', '/panel/')

    if request.user.is_authenticated:
        return redirect(next_url)

    if request.method == 'POST':
        username = request.POST.get('username')
        password = request.POST.get('password')

        user = authenticate(username=username, password=password)

        if user is not None:
            if user.is_active and Participant.exists(user):
                login(request, user)
                return redirect(next_url)
            else:
                context['error_message'] = 'Пользователь не активен'
        else:
            context['error_message'] = 'Неправильный логин или пароль'

        # Сохранить для удобства
        context['data']['username'] = username

    return render(request, 'panel/login.html', context)


def signup_view(request):

    context = {
        'app_version': settings.APP_VERSION,
        'error_message': None,
        'data': {},
        'created': False
    }

    next_url = request.GET.get('next', '/panel/')

    if request.user.is_authenticated:
        return redirect(next_url)

    if request.method == 'POST':
        name = request.POST.get('name')
        surname = request.POST.get('surname')
        email = request.POST.get('email').lower()
        password = request.POST.get('password')
        password2 = request.POST.get('password2')

        # Сохранить для удобства
        context['data']['name'] = name
        context['data']['surname'] = surname
        context['data']['email'] = email

        if password != password2:
            context['error_message'] = 'Пароли не совпадают'
            return render(request, 'panel/signup.html', context)

        if Participant.email_exists(email):
            context['error_message'] = 'Пользователь с данным email уже существует'
            return render(request, 'panel/signup.html', context)

        user = User.objects.create_user(username=email, password=password)
        Participant.objects.create(
            user=user,
            name=name,
            surname=surname,
            email=email)

        login(request, user)

        return redirect(next_url)

    return render(request, 'panel/signup.html', context)
