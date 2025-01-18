from flask import Flask, render_template, request, redirect, session
import uuid
from models import Round, Player

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
        game_uuid = uuid.uuid4()
        player_count = int(request.form.get('player_count'))
        players = [Player() for x in range(player_count)]
        games[game_uuid] = Round(players)
        session['game_uuid'] = game_uuid
        return redirect('/rozgrywka')
    else:
        return render_template('game_settings.html')

@app.get('/rozgrywka')
def game_get():
    game_uuid = session.get('game_uuid')
    if game_uuid is None or game_uuid not in games.keys():
        return redirect('/ustawienia-rozgrywki')

    round1 = games[game_uuid]
    return render_template('game.html', round=round1)

@app.post('/rozgrywka')
def game_post():
    if session.get('game_uuid') is None:
        return redirect('/ustawienia-rozgrywki')

    game = games[session.get('game_uuid')]
    card = request.form.get('card')
    return f"Wybrano kartę: {card}"


if __name__ == "__main__":
    app.run(debug=True, port=12209)