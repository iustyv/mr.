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

function createMultiplayerGame(event) {
    let game_mode = document.getElementById('game_mode').value;
    if (game_mode === 'multiplayer') {
        event.preventDefault();
        //socket.connect();
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