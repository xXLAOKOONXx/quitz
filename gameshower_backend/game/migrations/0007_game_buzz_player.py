# Generated by Django 5.1.4 on 2025-02-03 19:21

import django.db.models.deletion
from django.db import migrations, models


class Migration(migrations.Migration):

    dependencies = [
        ('game', '0006_game_buzzers_locked'),
    ]

    operations = [
        migrations.AddField(
            model_name='game',
            name='buzz_player',
            field=models.ForeignKey(blank=True, null=True, on_delete=django.db.models.deletion.CASCADE, related_name='buzz_player', to='game.gameparticipant'),
        ),
    ]
