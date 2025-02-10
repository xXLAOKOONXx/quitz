# Generated by Django 5.1.4 on 2025-02-03 09:52

import game.models
from django.db import migrations, models


class Migration(migrations.Migration):

    dependencies = [
        ('game', '0004_remove_currentview_jepardy_table_id_and_more'),
    ]

    operations = [
        migrations.AddField(
            model_name='game',
            name='moderator_key',
            field=models.CharField(default=game.models.generate_private_key, max_length=100, null=True),
        ),
        migrations.AddField(
            model_name='game',
            name='spectator_key',
            field=models.CharField(default=game.models.generate_private_key, max_length=100, null=True),
        ),
    ]
