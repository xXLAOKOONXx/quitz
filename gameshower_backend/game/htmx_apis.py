from django.shortcuts import render
from .models import GameQuestion, JepardyQuestion, JepardyColumn, JepardyTable, Game, GameParticipant
import json
from django.http import HttpRequest

def add_quiz_table(request):
    quiz_tables = JepardyTable.objects.all()
    context = {
        'quiz_tables': [{
            'id':table.id,
            'name':table.name,
        } for table in quiz_tables]
    }
    return render(request, 'creation/add_quiz_table_partial.html', context=context)

def create_game(request: HttpRequest):
    p = request.POST
    game_name = p['game-name']
    selected_quiz_tables = p.getlist('selected-quiz-table')
    new_quiz_table_names = p.getlist('new-quiz-table-name')
    for i in range(len(selected_quiz_tables)):
        if selected_quiz_tables[i] == 'create':
          new_quiz_table_name = new_quiz_table_names[i]
          new_quiz_table = JepardyTable.objects.create(name=new_quiz_table_name)
          new_quiz_table.save()
          selected_quiz_tables[i] = new_quiz_table.id
    quiz_tables = [JepardyTable.objects.get(id=table_id) for table_id in selected_quiz_tables]
    game = Game.objects.create(name=game_name)
    game.jepardytables.set(quiz_tables)
    game.save()
    return render(request, 'creation/game_page.html', context={'game_id': game.id, 'game_name': game_name})

def laod_quiz_table(request: HttpRequest):
    p = request.POST
    print(f'p: {p}')
    quiz_table_id = p.get('quiz-table')
    quiz_table = JepardyTable.objects.get(id=quiz_table_id)
    
    return render(request, 'creation/quiz_table_partial.html', context={'quiz_table': quiz_table})
    
