from flask import Flask, render_template, request, redirect, session, url_for
import uuid
from models import Round, Player, Card, AiPlayer, HumanPlayer, MultiplayerRound, LocalRound
import logging

app = Flask(__name__)
app.config['SECRET_KEY'] = 'P7D64Zl1mJywHZLButdsmmLk'

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

    players = []
    if game_mode == 'bot':
        players = [HumanPlayer('human')]
        players.extend([AiPlayer('player'+'%d'%(x+2)) for x in range(player_count-1)])
    elif game_mode == 'hotseat':
        players = [HumanPlayer('player' + '%d' % (x + 1)) for x in range(player_count)]
    elif game_mode == 'multiplayer':
        players = [HumanPlayer()]

    game_uuid = uuid.uuid4()

    if game_mode == 'multiplayer':
        game = MultiplayerRound(players, player_count)
        active_join_codes[game.join_code] = game_uuid
    else:
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

    return render_template('game.html', round=round1)

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

@app.post('/dolacz_do_gry')
def join_game():
    join_code = request.form.get('join_code')
    if join_code is None:
        return redirect(url_for('game_settings_get'))

    game_uuid = active_join_codes.get(join_code)
    if game_uuid is None or game_uuid not in games.keys():
        logging.error('Game uuid not found')
        return redirect(url_for('game_settings_get'))

    game = games[game_uuid]
    game.join(HumanPlayer())
    session['game_uuid'] = game_uuid

    if game.is_full_room():
        active_join_codes.pop(join_code)

    return redirect(url_for('game_get'))


if __name__ == "__main__":
    app.run(debug=True, port=12209)