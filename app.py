from flask import Flask, render_template, request, redirect, session, url_for
from flask_socketio import SocketIO, emit, join_room, rooms
import uuid
from models import Round, Player, Card, AiPlayer, HumanPlayer, MultiplayerRound, LocalRound
import logging

app = Flask(__name__)
app.config['SECRET_KEY'] = 'P7D64Zl1mJywHZLButdsmmLk'
app.config['DEBUG'] = True

socketio = SocketIO(app)

games = {}
active_join_codes = {}

@app.route('/')
def index():
    return render_template('index.html')

@app.route('/zasady')
def rules():
    return render_template('rules.html')

@app.get('/ustawienia-rozgrywki')
def game_settings_get():
    return render_template('game_settings.html')

@app.post('/ustawienia-rozgrywki')
def game_settings_post():
    game_mode = request.form.get('game_mode')
    player_count = int(request.form.get('player_count'))

    if game_mode is None or player_count is None:
        return redirect(url_for('game_settings_get'))

    if game_mode == 'multiplayer':
        return redirect(url_for('game_get'))

    players = []
    if game_mode == 'bot':
        players = [HumanPlayer('human')]
        players.extend([AiPlayer('player'+'%d'%(x+2)) for x in range(player_count-1)])
    elif game_mode == 'hotseat':
        players = [HumanPlayer('player' + '%d' % (x + 1)) for x in range(player_count)]

    game_uuid = str(uuid.uuid4())
    game = LocalRound(players)

    games[game_uuid] = game
    session['game_uuid'] = game_uuid
    return redirect(url_for('game_get'))

@app.get('/rozgrywka')
def game_get():
    game_uuid = session.get('game_uuid')
    if game_uuid is None or game_uuid not in games.keys():
        logging.error('Game uuid not found')
        return redirect('/ustawienia-rozgrywki')

    round1 = games[game_uuid]
    if not isinstance(round1, MultiplayerRound):
        return render_template('game.html', round=round1)

    if not round1.is_full_room():
        return render_template('waiting_for_players.html', round=round1)

    if not round1.is_started:
        round1.start()

    return render_template('multiplayer_game.html', round=round1)

@app.post('/rozgrywka')
def game_post():
    game_uuid = session.get('game_uuid')
    if game_uuid is None or game_uuid not in games.keys():
        return redirect('/ustawienia-rozgrywki')

    card = request.form.get('card')
    game = games[game_uuid]

    if not card:
        if request.form.get('skip'):
            game.play(skip = True)
        return redirect(url_for('game_get'))

    card = Card.create_from_form(card)
    logging.error("", card)
    if not game.is_valid_move(card):
        return redirect(url_for('game_get'))

    game.play(card=card)
    return redirect(url_for('game_get'))

@app.get('/bot_move')
def bot_move():
    game_uuid = session.get('game_uuid')
    if game_uuid is None or game_uuid not in games.keys():
        return redirect('/ustawienia-rozgrywki')

    game = games[game_uuid]
    game.handle_ai_players()

    return redirect(url_for('game_get'))

@app.get('/sesja')
def save_to_session():
    args = request.args

    for key, value in args.items():
        if key != 'redirect_url':
            session[key] = value

    redirect_url = args.get('redirect_url', '/')
    return redirect(redirect_url)

@socketio.on('create_game')
def handle_create_game(player_count):
    player = HumanPlayer()
    game_uuid = str(uuid.uuid4())

    game = MultiplayerRound([player], int(player_count))
    games[game_uuid] = game
    active_join_codes[game.join_code] = game_uuid

    join_room(game_uuid)
    print(f"user joined room {rooms(request.sid)}")

    socketio.emit('redirect',
                  url_for('save_to_session',
                          redirect_url='/rozgrywka',
                          player_name=player.name,
                          game_uuid=game_uuid),
                  to=request.sid)

@socketio.on('join_game')
def handle_join_game(join_code):
    if join_code is None:
        emit('redirect', url_for('game_settings_get'), to=request.sid)
        return

    game_uuid = active_join_codes.get(join_code)
    if game_uuid is None or game_uuid not in games.keys():
        logging.error('Game uuid not found')
        emit('redirect', url_for('game_settings_get'), to=request.sid)
        return

    game = games[game_uuid]
    player = HumanPlayer()
    game.join(player)
    join_room(game_uuid)
    print(f"user joined room {rooms(request.sid)}")
    print(game_uuid)

    if game_uuid in socketio.server.manager.rooms.get('/', {}):
        print(f"Emitting 'reload' to room: {game_uuid}")
    else:
        print(f"Room {game_uuid} does not exist!")
    emit('reload', broadcast=True)

    if game.is_full_room():
        active_join_codes.pop(join_code)

    emit('redirect',
                  url_for('save_to_session',
                          redirect_url='/rozgrywka',
                          player_name=player.name,
                          game_uuid=game_uuid),
                  to=request.sid)


if __name__ == "__main__":
    socketio.run(app, debug=True, port=12209)