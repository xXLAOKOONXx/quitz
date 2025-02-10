from django.urls import path
from . import views

urlpatterns = [
    path('', views.welcome_page, name='welcome_page'),
    path('start-game', views.start_game, name='start_game'),
    path('create-game', views.create_game, name='create_game'),
    path('timer', views.timer, name='timer'),
    path('player', views.player_page, name='player_page'),
    path('game_keys/<int:game_id>/', views.game_keys_page, name='game_keys'),
    path('moderator', views.moderator_page, name='moderator_page'),
]
