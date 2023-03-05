from django.urls import path

from . import views

urlpatterns = [
    path('', views.index, name='index'),
    path('send_message/', views.send_message, name='send-message'),
    path('clear_messages/', views.clear_messages, name='clear-messages'),
    path('show_next_response', views.show_next_response, name='show-next-response'),
]
