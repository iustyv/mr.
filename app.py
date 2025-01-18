from flask import Flask, render_template, request, redirect, session, url_for
import uuid
from models import Round, Player, Card

app = Flask(__name__)
app.config['SECRET_KEY'] = 'P7D64Zl1mJywHZLButdsmmLk'

games = {}

@app.route('/')
def index():
    return render_template('index.html')

@app.route('/zasady')
def rules():
    return render_template('rules.html')

@app.route('/ustawienia-rozgrywki', methods=['GET', 'POST'])
def game_settings():
    if request.method == 'POST':
        return start_game()

    return render_template('game_settings.html')

def start_game():
    game_uuid = uuid.uuid4()
    player_count = int(request.form.get('player_count'))
    players = [Player('player'+'%d'%(x+1)) for x in range(player_count)]
    games[game_uuid] = Round(players)
    session['game_uuid'] = game_uuid
    return redirect(url_for('game_get'))

@app.get('/rozgrywka')
def game_get():
    game_uuid = session.get('game_uuid')
    if game_uuid is None or game_uuid not in games.keys():
        return redirect('/ustawienia-rozgrywki')

    round1 = games[game_uuid]
    return render_template('game.html', round=round1)

@app.post('/rozgrywka')
def game_post():
    game_uuid = session.get('game_uuid')
    if game_uuid is None or game_uuid not in games.keys():
        return redirect('/ustawienia-rozgrywki')

    card = request.form.get('card')
    if not card:
        return redirect(url_for('game_get'))

    game = games[game_uuid]
    card = Card(card[0], card[1:])
    if not game.is_valid_move(card):
        return redirect(url_for('game_get'))

    game.play(card)
    return redirect(url_for('game_get'))


if __name__ == "__main__":
    app.run(debug=True, port=12209)