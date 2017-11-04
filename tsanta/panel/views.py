from django.shortcuts import render
from django.conf import settings


def index_view(request):

    context = {
        'app_version': settings.APP_VERSION
    }

    return render(request, 'panel/index.html', context)
