from django.urls import path
from . import consumers

websocket_urlpatterns = [
    path('ws/game/', consumers.GameConsumer.as_asgi()),
    path('ws/moderator/', consumers.ModeratorConsumer.as_asgi()),
    path('ws/player/', consumers.PlayerConsumer.as_asgi()),
    path('ws/admin/', consumers.AdminConsumer.as_asgi()),
]
