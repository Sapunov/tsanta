from django.conf.urls import url

from panel import views


urlpatterns = [
    url('^auth/login$', views.loginView),
    url('^auth/logout$', views.logoutView),
    url('^', views.index_view)
]
