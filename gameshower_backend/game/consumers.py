import json
import asyncio
from channels.generic.websocket import WebsocketConsumer
from django.shortcuts import get_object_or_404
from .models import Game, GameParticipant, JepardyQuestion
from django.template.loader import render_to_string
from asgiref.sync import async_to_sync
from .settings import JEPARDY_LOOSE_FACTOR

class AdminConsumer(WebsocketConsumer):
    def connect(self):
        self.game = None
        self.accept()
    
    def disconnect(self, close_code):
        pass
    
    def receive(self, text_data):
        print('Received data: ', text_data)
        json_data = json.loads(text_data)
        print('Received JSON data: ', json_data)
        match json_data.get('type'):
            case 'create-game':
                self.create_game(json_data)

    def create_game(self, json_data: dict):
        print('Creating game with data: ', json_data)
        player_names = json_data.get('player_names', [])
        game_name = json_data.get('game_name', 'New Game')

        new_game = Game.objects.create()
        new_game.name = game_name
        new_game.save()
        for name in player_names:
            participant = GameParticipant(name=name, game=new_game)
            participant.save()
        self.game = new_game
        self.send(text_data=json.dumps({'game_id': new_game.id}))

def switch_to_question_view(game: Game, question_id: int):
    game.current_view.page = 'TextQuestion'
    jepardy_question = JepardyQuestion.objects.get(id=question_id)
    game.current_view.question_id = jepardy_question.question
    game.current_view.save()
    jepardy_question.is_active = True
    jepardy_question.save()

class GameConsumer(WebsocketConsumer):
    """
    GameConsumer is a WebSocket consumer that handles real-time updates and interactions for a game.
    Properties:
        game (Game | None): The current game instance.
        game_group_name (str): The name of the game group for WebSocket communication.
        user_id (str): The ID of the user connected to the WebSocket.
    WebSocket Connection Methods:
        disconnect(code): Handles the disconnection of the WebSocket.
    Game Group Methods:
        enter_game_group(): Adds the WebSocket to the game group.
        leave_game_group(): Removes the WebSocket from the game group.
    HTML Update Methods:
        send_player_score_setup(): Sends the initial player score setup to the client.
        send_player_scores(): Sends the player scores to the client.
        player_buzzed(): Sends the buzzer status to the client.
        push_question_text(): Sends the current question text to the client.
        push_answer_text(): Sends the current answer text to the client.
        push_timer(count): Sends the timer count to the client.
    Game Group Trigger Methods:
        trigger_enter_group_event(): Triggers an event when a user enters the group.
        trigger_leave_group_event(): Triggers an event when a user leaves the group.
        trigger_buzz_update_event(): Triggers an event to update the buzzer status.
        trigger_view_update_event(): Triggers an event to update the view.
        trigger_question_view_update_event(): Triggers an event to update the question view.
        trigger_score_update_event(): Triggers an event to update the scores.
        trigger_push_answer_event(): Triggers an event to update the answer text.
        trigger_timer_update_event(count): Triggers an event to update the timer count.
    Game Group Event Handlers:
        question_view_update(event): Handles the question view update event.
        score_update(event): Handles the score update event.
        answer_text_update(event): Handles the answer text update event.
        timer_update(event): Handles the timer update event.
        view_update(event): Handles the view update event.
        user_entered(event): Handles the user entered event.
        user_left(event): Handles the user left event.
        buzz_update(event): Handles the buzz update event.
    """

    #region Properties
    game: None | Game = None
    """The current game instance."""
    @property
    def game_group_name(self):
        """The name of the game group for WebSocket communication."""
        return f'game_{self.game.id}'
    user_id = 'unknown'
    """The ID of the user connected to the WebSocket."""
    #endregion

    #region websocket connection
    def disconnect(self, code):
        """Handles the disconnection of the WebSocket."""
        self.leave_game_group()
    #endregion

    #region gamegroup
    def enter_game_group(self):
        """Adds the WebSocket to the game group. The game property needs to be set."""
        async_to_sync(self.channel_layer.group_add)(self.game_group_name, self.channel_name)

    def leave_game_group(self):
        """Removes the WebSocket from the game group."""
        if self.channel_name in self.channel_layer.groups.get(self.game_group_name, set()):
            self.trigger_leave_group_event()
            async_to_sync(self.channel_layer.group_discard)(self.game_group_name, self.channel_name)
    #endregion
    
    #region html updates
    def send_player_score_setup(self):
        """Sends the initial player score setup to the client."""
        context = {
            'participants': [participant.to_json() for participant in self.game.participants.all()]
        }
        self.send(text_data=render_to_string('game/score_setup_partial.html', context=context))
        self.send_player_scores()

    def send_player_scores(self):
        """Sends the player scores to the client."""
        for participant in self.game.participants.all():
            self.send(text_data=render_to_string('game/score_partial.html', {'id': participant.id, 'score': participant.score}))
    
    def push_question_text(self):
        """Sends the current question text to the client."""
        if self.game.current_view.question_visible:
            html = render_to_string('player/question_text_partial.html', {'question_text': self.game.current_view.question_id.question})
            self.send(text_data=html)

    def push_answer_text(self):
        """Sends the current answer text to the client."""
        html = render_to_string('game/question_partials/answer_wrap.html', {'answer_text': self.game.current_view.question_id.answer, 'answer_visible': self.game.current_view.answer_visible})
        self.send(text_data=html)

    def push_timer(self, count):
        """Sends the timer count to the client."""
        html = render_to_string('game/question_partials/timer_wrap.html', {'timer': count})
        self.send(text_data=html)
    #endregion

    #region game group triggers
    def trigger_enter_group_event(self):
        """Triggers an event for when a user enters the group."""
        event = {
            'type': 'user_entered',
            'user_id': self.user_id,
        }
        self.send_game_event(event)

    def trigger_leave_group_event(self):
        """Triggers an event for when a user leaves the group."""
        event = {
            'type': 'user_left',
            'user_id': self.user_id,
        }
        self.send_game_event(event)

    def trigger_buzz_update_event(self):
        """Triggers an event to update the buzzer status."""
        event = {
            'type': 'buzz_update',
        }
        self.send_game_event(event)

    def trigger_view_update_event(self):
        """Triggers an event to update the complete view."""
        event = {
            'type': 'view_update',
        }
        self.send_game_event(event)

    def trigger_question_view_update_event(self):
        """Triggers an event to update the question view."""
        event = {
            'type': 'question_view_update',
        }
        self.send_game_event(event)

    def trigger_score_update_event(self):
        """Triggers an event to update the scores."""
        event = {
            'type': 'score_update',
        }
        self.send_game_event(event)

    def trigger_push_answer_event(self):
        """Triggers an event to update the answer text."""
        event = {
            'type': 'answer_text_update',
        }
        self.send_game_event(event)
    
    def trigger_timer_update_event(self, count: int):
        """Triggers an event to update the timer count."""
        event = {
            'type': 'timer_update',
            'count': count,
        }
        self.send_game_event(event)

    def send_game_event(self, event):
        """Sends a game event to the game group."""
        async_to_sync(self.channel_layer.group_send)(
            self.game_group_name,
            event
        )
    #endregion

    #region game group event handlers
    def question_view_update(self, event):
        """Handles the question view update event."""
        self.push_question_text()

    def score_update(self, event):
        """Handles the score update event."""
        self.send_player_scores()

    def answer_text_update(self, event):
        """Handles the answer text update event."""
        self.push_answer_text()

    def timer_update(self, event):
        """Handles the timer update event."""
        self.push_timer(count=event.get('count'))

    def view_update(self, event):
        """Handles the view update event."""
        pass

    def user_entered(self, event):
        """Handles the user entered event."""
        pass

    def user_left(self, event):
        """Handles the user left event."""
        pass

    def buzz_update(self, event):
        """Handles the buzz update event."""
        pass
    #endregion


class PlayerConsumer(GameConsumer):
    #region Properties
    game_participant_id: None | int = None
    """The ID of the game participant."""
    @property
    def game_participant(self) -> None | GameParticipant:
        """The game participant instance."""
        if self.game_participant_id is None:
            return None
        return GameParticipant.objects.get(id=self.game_participant_id)
    @property
    def game(self):
        """The current game instance."""
        if self.game_participant is None:
            return None
        return self.game_participant.game
    @property
    def user_id(self):
        """The ID of the user connected to the WebSocket."""
        return self.game_participant_id
    #endregion

    #region websocket connection
    def connect(self):
        """Initializes the connection of the WebSocket."""
        self.accept()
        self.push_login()
    
    def disconnect(self, close_code):
        """Handles the disconnection of the WebSocket."""
        super().disconnect(close_code)
    
    def receive(self, text_data):
        """Handles the reception of data from the WebSocket."""
        json_data = json.loads(text_data)
        match json_data.get('type'):
            case 'login':
                self.login(json_data.get('gameCode'))
            case 'question-click':
                return
            case 'buzzer-click':
                self.buzz()
    #endregion

    #region html updates
    def push_view(self):
        """Pushes the current view to the client."""
        if self.game_participant is None:
            self.push_login()
            return
        if self.game_participant.game.current_view.page == 'JepardyTable':
            self.push_jepardy_table_view()
            return
        if self.game_participant.game.current_view.page == 'TextQuestion':
            self.push_question()
            return

    def push_login(self):
        """Pushes the login view to the client."""
        html = render_to_string('player/login_partial.html')
        self.send(text_data=html)

    def push_jepardy_table_view(self):
        """Pushes the jepardy table view to the client."""
        if self.game_participant is None:
            self.push_login()
            return
        html = render_to_string('game/quiztable_partial.html', {'table': self.game.current_view.jepardy_table})
        self.send(text_data=html)
        
    def push_question(self):
        """Pushes the question view to the client."""
        html = render_to_string('player/question_partial.html')
        self.send(text_data=html)
        self.push_question_text()
        self.update_buzzer()
        self.push_answer_text()

    def push_question_text(self):
        """Pushes the question text to the client."""
        if self.game.current_view.question_visible:
            html = render_to_string('player/question_text_partial.html', {'question_text': self.game_participant.game.current_view.question_id.question})
            self.send(text_data=html)

    def update_buzzer(self):
        """Updates the buzzer status."""
        html = render_to_string('player/buzzer_partial.html', {'disabled': self.game_participant.round_lock or self.game_participant.game.buzzers_locked})
        self.send(text_data=html)
    #endregion

    #region websocket actions
    def login(self, game_code:str):
        """Handles the login action."""
        try:
            participant = GameParticipant.objects.get(private_key=game_code)
            self.game_participant_id = participant.id
            self.push_view()
            self.enter_game_group()
            print('Login Success, setting up scores next')
            self.send_player_score_setup()
        except GameParticipant.DoesNotExist:
            self.push_login()

    def buzz(self):
        """Handles the buzzer action."""
        participant = self.game_participant
        if participant is None:
            return
        if participant.round_lock or participant.game.buzzers_locked:
            return
        participant.game.buzzers_locked = True
        participant.game.save()
        participant.round_lock = True
        participant.save()
        participant.game.buzz_player_id = participant.id
        participant.game.save()
        self.trigger_buzz_update_event()
    #endregion

    #region game group event handlers
    def buzz_update(self, event):
        """Handles the buzz update event."""
        self.update_buzzer()

    def view_update(self, event):
        """Handles the view update event."""
        self.push_view()
    #endregion

class ModeratorConsumer(GameConsumer):
    #region Properties
    game_id = None
    """The ID of the game."""
    @property
    def game(self):
        """The current game instance."""
        return get_object_or_404(Game, id=self.game_id)
    #endregion

    #region websocket connection
    def connect(self):
        """Initializes the connection of the WebSocket."""
        self.accept()
        self.push_login()
    
    def disconnect(self, close_code):
        """Handles the disconnection of the WebSocket."""
        super().disconnect(close_code)
    
    def receive(self, text_data):
        """Handles the reception of data from the WebSocket."""
        json_data = json.loads(text_data)
        match json_data.get('type'):
            case 'login':
                self.login(json_data.get('gameCode'))
            case 'question-click':
                switch_to_question_view(self.game, json_data.get('question_id'))
                self.trigger_view_update_event()
            case 'show-question-click':
                game = self.game
                game.current_view.question_visible = not game.current_view.question_visible
                game.current_view.save()
                self.trigger_view_update_event()
            case 'show-answer-click':
                game = self.game
                game.current_view.answer_visible = not game.current_view.answer_visible
                game.current_view.save()
                self.trigger_push_answer_event()
            case 'player-buzzer-lock':
                player_id = json_data.get('player_id')
                player = GameParticipant.objects.get(id=player_id)
                player.round_lock = not player.round_lock
                player.save()
                self.trigger_buzz_update_event()
            case 'toggle-all-buzzers':
                game = self.game
                game.buzzers_locked = not game.buzzers_locked
                game.save()
                self.trigger_buzz_update_event()
            case 'rate-answer':
                self.rate_answer(json_data)
            case 'exit-question':
                self.exit_question()
            case 'timer-update':
                self.handle_timer_update(json_data.get('count'))
    #endregion

    #region html updates    
    def push_view(self):
        """Pushes the current view to the client."""
        if self.game_id is None:
            self.push_login()
            return
        if self.game.current_view.page == 'JepardyTable':
            self.push_quiz_table_view()
            return
        if self.game.current_view.page == 'TextQuestion':
            self.push_question()
            return

    def push_login(self):
        """Pushes the login view to the client."""
        html = render_to_string('moderator/login_partial.html')
        self.send(text_data=html)

    def push_quiz_table_view(self):
        """Pushes the jepardy table view to the client."""
        if self.game_id is None:
            self.push_login()
            return
        html = render_to_string('game/quiztable_partial.html', {'table': self.game.current_view.jepardy_table})
        self.send(text_data=html)

    #region question
    def push_question(self):
        """Pushes the question view to the client."""
        html = render_to_string('moderator/question_partial.html')
        self.send(text_data=html)
        self.push_question_text()
        self.push_answer_text()
        self.send_player_score_setup()
        self.push_buzz_update()

    def push_question_text(self):
        """Pushes the question text to the client."""
        html = render_to_string('moderator/question_wrap.html', {'question_text': self.game.current_view.question_id.question, 'question_visible': self.game.current_view.question_visible})
        self.send(text_data=html)

    def push_buzz_update(self, event=None):
        """Updates the buzzer status."""
        game = self.game
        context = {
            'buzzers_locked': game.buzzers_locked,
            'buzz_player_id': game.buzz_player_id,
            'participants': [participant.to_json() for participant in game.participants.all()]
        }
        html = render_to_string('moderator/buzzer_partial.html', context=context)
        self.send(text_data=html)
        if game.buzz_player_id is not None:
            self.send(text_data=render_to_string('moderator/rate_answer_partial.html'))
        else:
            self.send(text_data='<div id="rate_answer_wrap" hx-swap="innerHTML"></div>')

    def push_answer_text(self, event=None):
        """Pushes the answer text to the client."""
        html = render_to_string('moderator/answer_wrap.html', {'answer_text': self.game.current_view.question_id.answer, 'answer_visible': self.game.current_view.answer_visible})
        self.send(text_data=html)
    #endregion
    #endregion

    #region websocket actions
    def login(self, game_code:str):
        """Handles the login action."""
        try:
            game = Game.objects.get(moderator_key=game_code)
            self.game_id = game.id
            self.push_view()
            self.enter_game_group()
            print('Login Success, setting up scores next')
            self.send_player_score_setup()
        except Game.DoesNotExist:
            self.push_login()

    
    def rate_answer(self, json_data):
        """Handles the rating of an answer."""
        game = self.game
        if game.current_view.question_id is None:
            return
        question = game.current_view.question_id
        
        jepardy_question = JepardyQuestion.objects.get(question=question)

        if game.buzz_player_id is None:
            return
        
        buzz_player = GameParticipant.objects.get(id=game.buzz_player_id)
        
        match json_data.get('value'):
            case 'true':
                buzz_player.score += jepardy_question.points
                buzz_player.save()
                jepardy_question.is_played = True
                jepardy_question.save()
                self.trigger_score_update_event()
            case 'false':
                buzz_player.score -= jepardy_question.points * JEPARDY_LOOSE_FACTOR
                buzz_player.save()
                self.trigger_score_update_event()
            case 'skip':
                pass
        game.buzz_player_id = None
        game.save()
        self.trigger_buzz_update_event()

    def exit_question(self):
        """Handles the exit question action."""
        game = self.game
        question = game.current_view.question_id
        jep_question = JepardyQuestion.objects.get(question=question)
        jep_question.is_active = False
        jep_question.is_played = True
        jep_question.save()
        game.current_view.question_visible = False
        game.current_view.question_id = None
        game.current_view.page = 'JepardyTable'
        game.current_view.save()
        game.buzz_player_id = None
        game.buzzers_locked = False
        game.save()
        for participant in game.participants.all():
            participant.round_lock = False
            participant.save()
        self.trigger_view_update_event()

    def handle_timer_update(self, count):
        """Handles the timer update action."""
        self.trigger_timer_update_event(count)
        if count == 0 or count == '0':
            game = self.game
            game.buzzers_locked = True
            game.save()
            self.trigger_buzz_update_event()
    #endregion

    #region game group event handlers
    def view_update(self, event):
        """Handles the view update event."""
        self.push_view()

    def buzz_update(self, event=None):
        """Handles the buzz update event."""
        self.push_buzz_update()
    #endregion
