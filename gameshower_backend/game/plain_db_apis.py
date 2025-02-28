from django.http import JsonResponse
from game.models import GameQuestion, JepardyQuestion, JepardyColumn, JepardyTable, Game, GameParticipant
import json
from dataclasses import dataclass

@dataclass
class QuestionDTO:
  question: str
  answer: str
  points: int

@dataclass
class TableColumnDTO:
  name: str
  questions: list[QuestionDTO]

@dataclass
class TableDTO:
  name: str
  columns: list[TableColumnDTO]

@dataclass
class GameDTO:
  name: str
  tables: list[TableDTO]

@dataclass
class ParticipantDTO:
  name: str

@dataclass
class GameCreatedDTO:
  game_id: int

def create_game_api(request):
  try:
    game_created_dto = create_game_from_json(request.body.decode('utf-8'))
  except ValueError as e:
    return JsonResponse({'error': str(e)}, status=400)
  return JsonResponse({'game_id': game_created_dto.game_id})

def create_game_from_json(json_str: str):
  data = json.loads(json_str)
  print(data)
  try:           
    game_dto = GameDTO(
      name=data['name'],
      tables=[
          TableDTO(
              name=table['name'],
              columns=[
                  TableColumnDTO(
                      name=column['name'],
                      questions=[
                          QuestionDTO(
                              question=question['question'],
                              answer=question['answer'],
                              points=question['points']
                          ) for question in column['questions']
                      ]
                  ) for column in table['columns']
              ]
          ) for table in data['tables']
      ]
    )
    participants = [ParticipantDTO(name=participant['name']) for participant in data['participants']]
  except Exception as e:
    try:
      game_dto = GameDTO(
        name=data['name'],
        tables=[
            TableDTO(
                name=table['name'],
                columns=[
                    TableColumnDTO(
                        name=column['name'],
                        questions=[
                            QuestionDTO(
                                question=question['question'],
                                answer=question['answer'],
                                points=question['points']
                            ) for question in [column['questions'][key] for key in column['questions'].keys()]
                        ]
                    ) for column in [table['columns'][key] for key in table['columns'].keys()]
                ]
            ) for table in [data['tables'][key] for key in data['tables'].keys()]
        ]
      )
      participants = [ParticipantDTO(name=participant['name']) for participant in [data['participants'][key] for key in data['participants'].keys()]]
    except Exception as e:
      raise ValueError(f"Invalid JSON format: {e}")
    
  return create_full_game(game_dto, participants)

def create_full_game(game: GameDTO, participants: list[ParticipantDTO]):
  game_model = Game.objects.create(name=game.name)
  for table in game.tables:
    table_model = JepardyTable.objects.create(name=table.name)
    for column in table.columns:
      column_model = JepardyColumn.objects.create(name=column.name)
      for question in column.questions:
        question_model = GameQuestion.objects.create(question=question.question, answer=question.answer)
        jepardy_question = JepardyQuestion.objects.create(question=question_model, points=question.points)
        column_model.questions.add(jepardy_question)
      column_model.save()
      table_model.columns.add(column_model)
    table_model.save()
    game_model.jepardytables.add(table_model)
  game_model.save()
  for participant in participants:
    participant_model = GameParticipant.objects.create(name=participant.name, game=game_model)
    participant_model.save()
  return GameCreatedDTO(game_id=game_model.id)