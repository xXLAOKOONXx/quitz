from typing import Literal
from django.db import models
import string
import random

def generate_private_key():
    return ''.join(random.choices(string.ascii_letters + string.digits, k=100))

class GameQuestion(models.Model):
    question = models.CharField(max_length=100)
    answer = models.CharField(max_length=100)

class JepardyQuestion(models.Model):
    question = models.ForeignKey(GameQuestion, on_delete=models.CASCADE)
    points = models.IntegerField()
    is_played = models.BooleanField()
    is_active = models.BooleanField()

class JepardyColumn(models.Model):
    name = models.CharField(max_length=100)
    questions = models.ManyToManyField(JepardyQuestion, related_name='columns')

class JepardyTable(models.Model):
    name = models.CharField(max_length=100)
    columns = models.ManyToManyField(JepardyColumn)

AVAILABLE_VIEW_PAGES = Literal['JepardyTable', 'TextQuestion']

class CurrentView(models.Model):
    page = models.CharField(max_length=100)
    question_visible = models.BooleanField(default=False)
    answer_visible = models.BooleanField(default=False)
    question_id = models.ForeignKey(GameQuestion, on_delete=models.CASCADE, null=True, blank=True)
    jepardy_table = models.ForeignKey(JepardyTable, on_delete=models.CASCADE, null=True, blank=True)

class Game(models.Model):
    name = models.CharField(max_length=100)
    jepardytables = models.ManyToManyField(JepardyTable, related_name='game')
    current_view = models.ForeignKey(CurrentView, on_delete=models.CASCADE, null=True, blank=True)
    moderator_key = models.CharField(max_length=100, default=generate_private_key, null=True) # TODO: Should be unique
    spectator_key = models.CharField(max_length=100, default=generate_private_key, null=True) # TODO: Should be unique
    buzzers_locked = models.BooleanField(default=True)
    buzz_player_id = models.IntegerField(null=True, blank=True)


class GameParticipant(models.Model):
    name = models.CharField(max_length=100)
    score = models.IntegerField(default=0)
    round_lock = models.BooleanField(default=False)
    private_key = models.CharField(max_length=100, default=generate_private_key, unique=True)
    game = models.ForeignKey(Game, on_delete=models.CASCADE, related_name='participants')

    def to_json(self):
        return {
            'id': self.id,
            'name': self.name,
            'score': self.score,
            'round_lock': self.round_lock
        }