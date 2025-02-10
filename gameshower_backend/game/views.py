from django.shortcuts import render
from django.http import JsonResponse
import json
import os
from .models import Game
from django.contrib.auth.decorators import login_required, user_passes_test

def admin_required(view_func):
    decorated_view_func = login_required(user_passes_test(lambda u: u.is_superuser)(view_func))
    return decorated_view_func

def index(request):
    return render(request, 'game/index.html')

def start_game(request):
    quiztables = get_quiztables()
    return render(request, 'game/start_game.html', {'quiztables': quiztables})

def timer(request):
    return render(request, 'game/timer.html')

def get_quiztables():
    with open(os.path.join(os.path.dirname(__file__), 'quiztables.json')) as f:
        return json.load(f)
    
def create_game(request):
    return render(request, 'game/create_game.html')

def player_page(request):
    return render(request, 'bases/player_base.html', {'page_title': 'Loading'})

def moderator_page(request):
    return render(request, 'bases/moderator_base.html', {'page_title': 'Loading'})

def welcome_page(request):
    return render(request, 'other/welcome.html', {'page_title': 'Welcome'})

@admin_required
def game_keys_page(request, game_id):
    desired_game = Game.objects.get(id=game_id)
    context = {
        'moderator_key': desired_game.moderator_key,
        'spectator_key': desired_game.spectator_key,
        'participants': [
            {
                'name': participant.name,
                'private_key': participant.private_key
            } for participant in desired_game.participants.all()
        ]
    }
    return render(request, 'game/game_keys.html', context=context)
