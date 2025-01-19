from flask import Flask, render_template, request, redirect, session, url_for
import uuid
from models import Round, Player, Card, AiPlayer, HumanPlayer
import logging

app = Flask(__name__)
app.config['SECRET_KEY'] = 'P7D64Zl1mJywHZLButdsmmLk'

games = {}

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
    game_mode = int(request.form.get('game_mode'))
    player_count = int(request.form.get('player_count'))

    if game_mode is None or player_count is None:
        return redirect(url_for('game_settings_get'))

    players = []
    if game_mode == 0:
        #players = [Player('player'+'%d'%1)]
        players = [HumanPlayer('human')]
        players.extend([AiPlayer('player'+'%d'%(x+2)) for x in range(player_count-1)])
    elif game_mode == 1:
        players = [HumanPlayer('player' + '%d' % (x + 1)) for x in range(player_count)]

    return start_game(players)

def start_game(players):
    game_uuid = uuid.uuid4()
    games[game_uuid] = Round(players)
    session['game_uuid'] = game_uuid
    return redirect(url_for('game_get'))

@app.get('/rozgrywka')
def game_get():
    game_uuid = session.get('game_uuid')
    if game_uuid is None or game_uuid not in games.keys():
        logging.error('Game uuid not found')
        return redirect('/ustawienia-rozgrywki')

    round1 = games[game_uuid]
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
    if not game.is_valid_move(card):
        return redirect(url_for('game_get'))

    game.play(card)
    return redirect(url_for('game_get'))


if __name__ == "__main__":
    app.run(debug=True, port=12209)