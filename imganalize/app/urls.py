from django.urls import path
from . import views
urlpatterns=[
    path("", views.home, name="home"),
    path("redir/", views.redir, name="redir"),
    path("history/", views.history_view, name="history")
]