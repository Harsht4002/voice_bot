from django.urls import path
from . import views

urlpatterns = [
    path('', views.index, name='index'),         # A simple view for testing
    path('', views.agent_home, name='agent_home'),
    path('websocket/', views.agent_websocket, name='websocket'),  # WebSocket endpoint for the AI agent
]
