from django.conf.urls import url

from panel import views


urlpatterns = [
    url('^login$', views.login_view),
    url('^logout$', views.logout_view),
    # url('^signup', views.signup_view),
    url('^', views.index_view)
]
