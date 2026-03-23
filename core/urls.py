from django.urls import path, re_path
from django.views.static import serve
from . import views

urlpatterns = [
    path('', views.index_view, name="index"),
    re_path(r'^web/(?P<path>.*)$', serve, {'document_root': './web'}),
    path('api/state', views.get_state, name='state'),
    path('api/toggle_listen', views.toggle_listen, name='toggle_listen'),
    path('api/send_command', views.send_command, name='send_command'),
]
