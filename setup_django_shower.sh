#!/bin/bash

# Create Django project
django-admin startproject gameshower_backend
cd gameshower_backend

# Create Django app
python manage.py startapp game

# Install dependencies
pip install channels django-cors-headers

# Update settings.py
cat <<EOL >> gameshower_backend/settings.py

INSTALLED_APPS += [
    'channels',
    'game',
    'corsheaders',
]

MIDDLEWARE.insert(0, 'corsheaders.middleware.CorsMiddleware')

CORS_ALLOWED_ORIGINS = [
    "http://localhost:8080",
]

ASGI_APPLICATION = 'gameshower_backend.asgi.application'

CHANNEL_LAYERS = {
    'default': {
        'BACKEND': 'channels.layers.InMemoryChannelLayer',
    },
}
EOL

# Create asgi.py
cat <<EOL > gameshower_backend/asgi.py
import os
from django.core.asgi import get_asgi_application
from channels.routing import ProtocolTypeRouter, URLRouter
from channels.auth import AuthMiddlewareStack
from game.routing import websocket_urlpatterns

os.environ.setdefault('DJANGO_SETTINGS_MODULE', 'gameshower_backend.settings')

application = ProtocolTypeRouter({
    "http": get_asgi_application(),
    "websocket": AuthMiddlewareStack(
        URLRouter(
            websocket_urlpatterns
        )
    ),
})
EOL

# Create routing.py
mkdir -p game
cat <<EOL > game/routing.py
from django.urls import path
from . import consumers

websocket_urlpatterns = [
    path('ws/game/', consumers.GameConsumer.as_asgi()),
    path('ws/timer/', consumers.TimerConsumer.as_asgi()),
]
EOL

# Create consumers.py
cat <<EOL > game/consumers.py
import json
import asyncio
from channels.generic.websocket import AsyncWebsocketConsumer

class GameConsumer(AsyncWebsocketConsumer):
    async def connect(self):
        await self.accept()

    async def disconnect(self, close_code):
        pass

    async def receive(self, text_data):
        data = json.loads(text_data)
        await self.send(text_data=json.dumps({
            'message': 'Received your message!'
        }))

class TimerConsumer(AsyncWebsocketConsumer):
    async def connect(self):
        await self.accept()
        await self.start_countdown()

    async def disconnect(self, close_code):
        pass

    async def start_countdown(self):
        for i in range(30, -1, -1):
            await self.send(text_data=json.dumps({
                'count': i
            }))
            await asyncio.sleep(1)
EOL

# Create views.py
cat <<EOL > game/views.py
from django.shortcuts import render
from django.http import JsonResponse
import json
import os

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
EOL

# Create urls.py for the app
cat <<EOL > game/urls.py
from django.urls import path
from . import views

urlpatterns = [
    path('', views.index, name='index'),
    path('start-game', views.start_game, name='start_game'),
    path('timer', views.timer, name='timer'),
]
EOL

# Include app URLs in project urls.py
cat <<EOL >> gameshower_backend/urls.py
from django.urls import path, include

urlpatterns += [
    path('', include('game.urls')),
]
EOL

# Create basic HTML templates
mkdir -p game/templates/game
cat <<EOL > game/templates/game/index.html
<!DOCTYPE html>
<html lang="en">
<head>
    <meta charset="UTF-8">
    <meta name="viewport" content="width=device-width, initial-scale=1.0">
    <title>Game Shower</title>
    <script src="https://unpkg.com/htmx.org@1.6.1"></script>
</head>
<body>
    <h1>Game Shower</h1>
    <div id="game-container">
        <button id="start-game" hx-get="/start-game" hx-swap="outerHTML">Start Game</button>
    </div>
    <script>
        const socket = new WebSocket('ws://localhost:8000/ws/game/');
        socket.onmessage = function(event) {
            const data = JSON.parse(event.data);
            console.log('Message from server:', data.message);
        };
    </script>
</body>
</html>
EOL

cat <<EOL > game/templates/game/start_game.html
<!DOCTYPE html>
<html lang="en">
<head>
    <meta charset="UTF-8">
    <meta name="viewport" content="width=device-width, initial-scale=1.0">
    <title>Start Game</title>
</head>
<body>
    <h1>Select a Quiztable</h1>
    <form action="/start-game" method="post">
        {% csrf_token %}
        <select name="quiztable">
            {% for quiztable in quiztables %}
                <option value="{{ quiztable }}">{{ quiztable }}</option>
            {% endfor %}
        </select>
        <button type="submit">Start Game</button>
    </form>
</body>
</html>
EOL

cat <<EOL > game/templates/game/timer.html
<!DOCTYPE html>
<html lang="en">
<head>
    <meta charset="UTF-8">
    <meta name="viewport" content="width=device-width, initial-scale=1.0">
    <title>Timer</title>
</head>
<body>
    <h1>Countdown Timer</h1>
    <div id="timer">30</div>
    <script>
        const socket = new WebSocket('ws://localhost:8000/ws/timer/');
        socket.onmessage = function(event) {
            const data = JSON.parse(event.data);
            document.getElementById('timer').innerText = data.count;
        };
    </script>
</body>
</html>
EOL

# Create a sample quiztables.json file
cat <<EOL > game/quiztables.json
[
    {
        "name": "Sample Quiztable",
        "topics": [
            {
                "name": "Topic 1",
                "questions": [
                    {"question": "Question 1", "answer": "Answer 1"},
                    {"question": "Question 2", "answer": "Answer 2"},
                    {"question": "Question 3", "answer": "Answer 3"},
                    {"question": "Question 4", "answer": "Answer 4"},
                    {"question": "Question 5", "answer": "Answer 5"}
                ]
            },
            {
                "name": "Topic 2",
                "questions": [
                    {"question": "Question 1", "answer": "Answer 1"},
                    {"question": "Question 2", "answer": "Answer 2"},
                    {"question": "Question 3", "answer": "Answer 3"},
                    {"question": "Question 4", "answer": "Answer 4"},
                    {"question": "Question 5", "answer": "Answer 5"}
                ]
            }
        ]
    }
]
EOL

# Run migrations and start the server
python manage.py migrate
python manage.py runserver