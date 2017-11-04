from django.shortcuts import render, redirect


def index(request):

    context = {}

    return render(request, "front/index.html", context=context)


def application(request):

    context = {}

    return render(request, "front/application.html", context=context)


def thanks(request):

    context = {}

    return render(request, "front/thanks.html", context=context)
