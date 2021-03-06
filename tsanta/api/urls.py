from django.conf.urls import url
from api import views


urlpatterns = [
    url(r'^cities$', views.CityView.as_view()),
    url(r'^groups$', views.GroupView.as_view()),
    url(r'^groups/suggest$', views.suggest_group),
    url(r'^groups/(?P<group_id>[0-9]{1,10})$', views.GroupView.as_view()),
    url(r'^groups/check_slug$', views.check_slug),
    url(r'^events$', views.EventView.as_view()),
    url(r'^events/(?P<event_id>[0-9]{1,10})$', views.EventView.as_view()),
    url(r'^events/submit$', views.submit_questionnaire),
    url(r'^events/(?P<event_id>[0-9]{1,10})/participants$', views.event_participants),
    url(r'^events/(?P<event_id>[0-9]{1,10})/stat$', views.event_stat),
    url(r'^events/(?P<event_id>[0-9]{1,10})/assign$', views.assign_wards),
    url(r'^events/(?P<event_id>[0-9]{1,10})/send_confirms$', views.send_confirms),
    url(r'^events/(?P<event_id>[0-9]{1,10})/send_wards$', views.send_wards),
]
