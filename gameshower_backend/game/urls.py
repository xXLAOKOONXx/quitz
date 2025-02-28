from django.urls import path
from . import views, htmx_apis, plain_db_apis

urlpatterns = [
    path('', views.welcome_page, name='welcome_page'),
    path('start-game', views.start_game, name='start_game'),
    path('create-game', views.create_game, name='create_game'),
    path('timer', views.timer, name='timer'),
    path('player', views.player_page, name='player_page'),
    path('game_keys/<int:game_id>/', views.game_keys_page, name='game_keys'),
    path('moderator', views.moderator_page, name='moderator_page'),
    path('create-game-page', views.create_game_page, name='create_game_page'),
    path('quiz-tables', views.add_quiz_table, name='add_quiz_table'),
    path('api/add-quiz-table', htmx_apis.add_quiz_table, name='add_quiz_table'),
    path('api/create-game', htmx_apis.create_game, name='api_create_game'),
    path('api/load-quiz-table', htmx_apis.laod_quiz_table, name='load_quiz_table'),
    path('api/create-full-game/', plain_db_apis.create_game_api, name='create_full_game_api'),
    path('create/full-game/', views.create_full_game, name='create_full_game'),
]
