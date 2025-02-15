const socket = io('/', {autoConnect : false})
if(!socket.connected) {
    socket.connect()
}

socket.on('connect', () => {
    console.log('connected')
});

socket.on('reload', () => {
    console.log('reload')
    location.reload();
});


socket.on('redirect', (url) => {
    console.log(url)
    window.location.href = url;
});

socket.on("update_game", () => {
    htmx.trigger("#game-state", "ws-message");
});

socket.on('player_disconnected', (data) => {
    console.log('player_disconnected', data.player_id, data.player_name)
    console.log('inactive: {{ game.inactive_players }}')
    socket.emit('request_game_state_update')
    const element = document.getElementById('player-disconnected-msg')

    element.innerHTML = 'Player ' + data.player_name + ' has left the game.'
    element.style.display = 'block'
});

socket.on('player_connected', (data) => {
    console.log('player_connected', data.player_name)
    console.log('Game is full: {{ game.is_full_room() }}')
    console.log('inactive: {{ game.inactive_players }}')
    socket.emit('request_game_state_update')

    document.getElementById('player-disconnected-msg').style.display = 'none'
})

socket.on('request_game_state_update', () => {
    console.log('request_game_state_update received')
    socket.emit('request_game_state_update')
})

socket.on('update_game_state', (data) => {
    console.log('updated game state')
    document.getElementById('game-state').innerHTML = data.html;
    console.log('{{ game.current_round.move_queue[0].name }}')
});

function createMultiplayerGame(event) {
    let game_mode = document.getElementById('game_mode').value;
    if (game_mode === 'multiplayer') {
        event.preventDefault();
        let player_count = document.getElementById('player_count').value;
        socket.emit('create_game', player_count);
    }
}

function joinMultiplayerGame() {
    let join_code = document.getElementById('join_code').value;
    socket.emit('join_game', join_code);
}

function playCard() {
    console.log(selectedCards)
    let card = document.getElementById('card').value;
    if (card) {
        socket.emit('play_card', card);
    }
    selectedCards = []
}

function skipCard() {
    socket.emit('skip_move');
}

function restartGame() {
    socket.emit('restart_game');
}