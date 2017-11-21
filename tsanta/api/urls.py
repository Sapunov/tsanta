from django.conf.urls import url
from api import views


urlpatterns = [
    url(r'^cities$', views.CityView.as_view()),
    url(r'^groups$', views.GroupView.as_view()),
    url(r'^groups/suggest$', views.suggest_group),
    url(r'^groups/(?P<group_id>[0-9]{1,10})$', views.GroupView.as_view()),
    url(r'^groups/check_slug$', views.check_slug),
    url(r'^events$', views.EventView.as_view()),
    url(r'^events/(?P<event_id>[0-9]{1,10})$', views.EventView.as_view())
]
