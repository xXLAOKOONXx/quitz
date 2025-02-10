# Game Shower

This is a Quiz Game providing a webserver and web pages for a digital quiz experience. You can create your own Quiz, use the webserver for players to buzzer, keep score and show the questions in a fancy way.

## Start Up

You need to install `poetry` to use the python environment of this project.

With `poetry` installed you can install the python environment from within the root of this project:

```bash
poetry install
```

Create your own sqlite file and run migrations: (TODO: Check how this actually works)

```bash
poetry run python gameshower_backend/manage.py migrate
```

Spin up the development server:

```bash
poetry run python gameshower_backend/manage.py runserver
```

## Adding Data

You can create a superuser via:

```bash
poetry run python gameshower_backend/manage.py createsuperuser
```

With this superuser you can log into `your-instance/admin/` and access the database diorectly to create your quiz tables and questions. In future this might get a fancier UI.

If you are happy and want to play you can check `your-instance/game_keys/<int:game_id>/` with game_id being the database id of the game element. For each player you will get game_keys and there is also a key for the moderator.

## Run a game

Go to `your-instance/` to get hyperlinks to the login pages for players and the moderator.

In the login you need to enter a game_key to access the game.

Once logged in, the moderator has the control on what is shown to the players and players pretty much are only able to buzz if they are allowed to.

Maybe you need to change some fields in the current_view object of your game to show the quiz table. This will get improved on!
