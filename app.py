from flask import Flask, render_template, request, redirect, session, url_for, abort
from flask_socketio import SocketIO, emit, join_room, rooms
import uuid
from models import Round, Player, Card, AiPlayer, HumanPlayer, MultiplayerRound, LocalRound, MultiplayerGame, LocalGame
import logging

app = Flask(__name__)
app.config['SECRET_KEY'] = 'P7D64Zl1mJywHZLButdsmmLk'
app.config['DEBUG'] = True

socketio = SocketIO(app)

games = {}
active_join_codes = {}

@app.route('/')
def index():
    return redirect(url_for('game_settings_get'))

@app.route('/mr/game-rules')
def rules():
    return render_template('rules.html')

@app.route('/mr/credits')
def creds():
    return render_template('credits.html')

@app.get('/mr/game-settings')
def game_settings_get():
    return render_template('game_settings.html')

@app.post('/mr/game-settings')
def game_settings_post():
    game_mode = request.form.get('game_mode')
    player_count = int(request.form.get('player_count'))

    if game_mode is None or player_count is None:
        return redirect(url_for('game_settings_get'))

    if game_mode == 'multiplayer':
        return redirect(url_for('game_get'))

    players = {}
    if game_mode == 'bot':
        player_id = str(uuid.uuid4())
        players.update({player_id : HumanPlayer('human')})
        session['player_id'] = player_id
        for x in range(player_count - 1):
            players.update({str(uuid.uuid4()) : AiPlayer('player' + '%d' % (x + 2))})
    elif game_mode == 'hotseat':
        for x in range(player_count):
            players.update({str(uuid.uuid4()): HumanPlayer('player' + '%d' % (x + 1))})

    game_uuid = str(uuid.uuid4())
    game = LocalGame(players)

    games[game_uuid] = game
    session['game_uuid'] = game_uuid
    return redirect(url_for('game_get'))

@app.get('/mr/game')
def game_get():
    game_uuid = session.get('game_uuid')
    if game_uuid is None or game_uuid not in games.keys():
        logging.error('Game uuid not found')
        return redirect(url_for('game_settings_get'))

    game = games[game_uuid]
    if not isinstance(game, MultiplayerGame):
        my_player = game.current_round.get_current_player()
        if not my_player.is_playable:
            my_player = game.players[session.get('player_id')]
        return render_template('game.html', game=game, my_player = my_player)

    print(f"Users in {game_uuid}: {socketio.server.manager.rooms.get('/', {}).get(game_uuid, [])}")

    player_id = session.get('player_id')
    if not game.is_full_room() and not game.is_started:
        return render_template('waiting_for_players.html', game=game, my_player=game.players.get(player_id))

    if not game.is_started:
        game.start()

    return render_template('multiplayer_game.html', game=game, my_player=game.players.get(player_id))

@app.post('/mr/game')
def game_post():
    game_uuid = session.get('game_uuid')
    if game_uuid is None or game_uuid not in games.keys():
        return redirect(url_for('game_settings_get'))

    card = request.form.get('card')
    game = games[game_uuid]

    if not card:
        if request.form.get('skip'):
            game.play(skip = True)
        return redirect(url_for('game_get'))

    card = Card.create_from_form(card)
    logging.error("", card)
    if not game.current_round.is_valid_move(card):
        return redirect(url_for('game_get'))

    game.play(card=card)
    return redirect(url_for('game_get'))

@socketio.on('play_card')
def handle_play_card(card):
    game_uuid = session.get('game_uuid')
    player_id = session.get('player_id')
    if game_uuid is None or game_uuid not in games.keys() or not player_id:
        emit('redirect', url_for('game_settings_get'), to=request.sid)
        return

    game = games[game_uuid]

    if not card:
        emit('redirect', url_for('game_get'), to=request.sid)
        return
    card = Card.create_from_form(card)
    logging.error("", card)
    if game.current_round.is_valid_move(card):
        game.play(card=card)

    emit('request_game_state_update', to=game_uuid)

@socketio.on('request_game_state_update')
def handle_request_game_state_update():
    game_uuid = session.get('game_uuid')
    player_id = session.get('player_id')

    if not game_uuid or not player_id:
        return

    game = games[game_uuid]
    player = game.players.get(player_id)

    emit('update_game_state', {'html': render_template('game_state.html', game=game, my_player=player)})

@socketio.on('skip_move')
def handle_skip_move():
    game_uuid = session.get('game_uuid')
    if game_uuid is None or game_uuid not in games.keys():
        emit('redirect', url_for('game_settings_get'), to=request.sid)
        return

    game = games[game_uuid]
    if game.current_round.is_valid_move(skip=True):
        game.play(skip=True)
        emit('request_game_state_update', to=game_uuid)

@app.get('/bot_move')
def bot_move():
    game_uuid = session.get('game_uuid')
    if game_uuid is None or game_uuid not in games.keys():
        return redirect(url_for('game_settings_get'))

    game = games[game_uuid]
    if game.current_round.get_current_player().is_playable:
        return redirect(url_for('game_get'))

    game.play()

    return redirect(url_for('game_get'))

@app.get('/session')
def save_to_session():
    if request.referrer is None or request.referrer == request.url_root:
        print('manual access blocked')
        return redirect(url_for('game_settings_get'))
    args = request.args

    for key, value in args.items():
        if key != 'redirect_url':
            session[key] = value

    redirect_url = args.get('redirect_url', '/')
    return redirect(redirect_url)

@socketio.on('create_game', namespace='/')
def handle_create_game(player_count):
    player_id = str(uuid.uuid4())
    game_uuid = str(uuid.uuid4())
    player = HumanPlayer()

    game = MultiplayerGame({player_id : player}, int(player_count), player)

    games[game_uuid] = game
    active_join_codes[game.join_code] = game_uuid

    socketio.emit('redirect',
                  url_for('save_to_session',
                          redirect_url=url_for('game_get'),
                          player_id=player_id,
                          game_uuid=game_uuid),
                  to=request.sid)

@socketio.on('join_game', namespace='/')
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
    player_id = str(uuid.uuid4())
    game.join(player_id, HumanPlayer())

    if game_uuid in socketio.server.manager.rooms.get('/', {}):
        print(f"Users in {game_uuid}: {socketio.server.manager.rooms.get('/', {}).get(game_uuid, [])}")
        print(f"Emitting 'reload' to room: {game_uuid}")
    else:
        print(f"Room {game_uuid} does not exist!")

    if game.is_full_room():
        game.start()
        active_join_codes.pop(join_code)

    emit('reload', to=game_uuid)

    emit('redirect',
                  url_for('save_to_session',
                          redirect_url=url_for('game_get'),
                          player_id=player_id,
                          game_uuid=game_uuid),
                  to=request.sid)

@socketio.on('restart_game')
def handle_restart_game():
    game_uuid = session.get('game_uuid')
    if game_uuid is None or game_uuid not in games.keys():
        emit('redirect', url_for('game_settings_get'))
        return

    game = games[game_uuid]

    players = {}
    host_key = None
    for key, player in game.players.items():
        if player == game.game_host:
            host_key = key
        players[key] = HumanPlayer(player.name)

    game = MultiplayerGame(players, game.player_count, players[host_key])
    games[game_uuid] = game
    game.start()

    emit('request_game_state_update', to=game_uuid)

@socketio.on('join_room')
def handle_join_room():
    game_uuid = session.get('game_uuid')
    player_id = session.get('player_id')
    if game_uuid:
        join_room(game_uuid)

    game = games[game_uuid]

    game.inactive_players.discard(player_id)

    player_name = game.players.get(player_id).name
    emit('player_connected', {"player_id": player_id, "player_name": player_name}, to=game_uuid)


@socketio.on('disconnect')
def handle_disconnect():
    print(f"Client disconnected: {request.sid}")
    game_uuid = session.get('game_uuid')
    player_id = session.get('player_id')
    if not game_uuid or not player_id: return

    game = games[game_uuid]
    player_name = game.players.get(player_id).name
    if not isinstance(game, MultiplayerGame): return
    game.leave(player_id)

    emit('player_disconnected', {"player_id": player_id, "player_name": player_name}, to=game_uuid)


if __name__ == "__main__":
    socketio.run(app, debug=True, host='0.0.0.0', port=12209)