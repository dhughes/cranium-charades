#!/usr/bin/env python3
from flask import Flask, render_template_string, request
from flask_socketio import SocketIO, emit, join_room, leave_room
import json
import random
import time
from datetime import datetime, timedelta
import uuid

app = Flask(__name__)
app.config['SECRET_KEY'] = 'cranium-charades-secret-key'
socketio = SocketIO(app, cors_allowed_origins="*")

with open('words.json', 'r') as f:
    WORDS = json.load(f)

WORD_LISTS = {
    'running': ['running', 'walking', 'jumping', 'flying', 'swimming', 'climbing', 'dancing', 'singing'],
    'colors': ['red', 'blue', 'green', 'yellow', 'purple', 'orange', 'pink', 'brown'],
    'animals': ['cat', 'dog', 'bird', 'fish', 'elephant', 'lion', 'tiger', 'bear']
}

games = {}

def generate_game_code():
    adjectives = ['happy', 'sunny', 'bright', 'clever', 'swift', 'gentle', 'brave', 'kind',
                  'wise', 'calm', 'bold', 'cool', 'lucky', 'merry', 'quiet', 'rapid',
                  'sharp', 'smart', 'wild', 'young', 'zesty', 'eager', 'fancy', 'grand',
                  'jolly', 'lively', 'mighty', 'noble', 'proud', 'royal', 'super', 'vital',
                  'warm', 'zippy', 'sleek', 'slick', 'snappy', 'speedy', 'spry', 'sturdy']

    colors = ['red', 'blue', 'green', 'yellow', 'purple', 'orange', 'pink', 'cyan',
              'amber', 'jade', 'ruby', 'coral', 'mint', 'lime', 'navy', 'teal',
              'gold', 'silver', 'bronze', 'pearl', 'ivory', 'azure', 'crimson', 'indigo',
              'violet', 'magenta', 'maroon', 'olive', 'plum', 'tan', 'beige', 'khaki']

    nouns = ['fox', 'bear', 'wolf', 'deer', 'hawk', 'eagle', 'lion', 'tiger',
             'panda', 'koala', 'otter', 'seal', 'whale', 'shark', 'dolphin', 'penguin',
             'rabbit', 'squirrel', 'beaver', 'moose', 'elk', 'bison', 'zebra', 'giraffe',
             'monkey', 'gorilla', 'leopard', 'cheetah', 'panther', 'jaguar', 'lynx', 'cougar',
             'falcon', 'raven', 'crow', 'sparrow', 'robin', 'finch', 'wren', 'jay']

    while True:
        code = f"{random.choice(adjectives)}-{random.choice(colors)}-{random.choice(nouns)}"
        if code not in games:
            return code

def create_game():
    game_id = generate_game_code()
    games[game_id] = {
        'game_id': game_id,
        'players': {},
        'state': 'lobby',
        'current_guesser_id': None,
        'current_category': None,
        'current_word': None,
        'round_score': 0,
        'timer_start': None,
        'timer_duration': 60,
        'words_used_this_round': [],
        'last_activity': datetime.now()
    }
    return game_id

def get_next_word(game_id):
    game = games[game_id]
    category = game['current_category']
    available_words = [w for w in WORDS[category] if w not in game['words_used_this_round']]

    if not available_words:
        available_words = WORDS[category]
        game['words_used_this_round'] = []

    word = random.choice(available_words)
    game['words_used_this_round'].append(word)
    game['current_word'] = word
    return word

def get_game_state(game_id):
    if game_id not in games:
        return None

    game = games[game_id]
    players_list = []
    for pid, player in game['players'].items():
        players_list.append({
            'player_id': pid,
            'name': player['name'],
            'score': player['score'],
            'connected': player['connected']
        })

    time_remaining = None
    if game['timer_start']:
        elapsed = time.time() - game['timer_start']
        time_remaining = max(0, game['timer_duration'] - elapsed)

    return {
        'game_id': game_id,
        'players': players_list,
        'state': game['state'],
        'current_guesser_id': game['current_guesser_id'],
        'current_category': game['current_category'],
        'round_score': game['round_score'],
        'time_remaining': time_remaining,
        'categories': list(WORDS.keys())
    }

@app.route('/')
def index():
    return render_template_string(HTML_TEMPLATE)

@app.route('/game/<game_id>')
def game(game_id):
    return render_template_string(HTML_TEMPLATE)

@socketio.on('create_game')
def handle_create_game():
    game_id = create_game()
    emit('game_created', {'game_id': game_id})

@socketio.on('join_game')
def handle_join_game(data):
    game_id = data['game_id']
    player_name = data['player_name']

    if game_id not in games:
        emit('error', {'message': 'Game not found'})
        return

    player_id = str(uuid.uuid4())
    request.sid

    games[game_id]['players'][player_id] = {
        'name': player_name,
        'score': 0,
        'connected': True,
        'sid': request.sid
    }
    games[game_id]['last_activity'] = datetime.now()

    join_room(game_id)

    emit('joined_game', {
        'player_id': player_id,
        'game_state': get_game_state(game_id)
    })

    emit('player_joined', {
        'player_name': player_name,
        'game_state': get_game_state(game_id)
    }, room=game_id, skip_sid=request.sid)

@socketio.on('start_round')
def handle_start_round(data):
    game_id = data['game_id']
    player_id = data['player_id']

    if game_id not in games:
        emit('error', {'message': 'Game not found'})
        return

    game = games[game_id]
    game['state'] = 'category_selection'
    game['current_guesser_id'] = player_id
    game['round_score'] = 0
    game['words_used_this_round'] = []
    game['last_activity'] = datetime.now()

    emit('round_started', {
        'guesser_name': game['players'][player_id]['name'],
        'game_state': get_game_state(game_id)
    }, room=game_id)

@socketio.on('select_category')
def handle_select_category(data):
    game_id = data['game_id']
    category = data['category']

    if game_id not in games:
        emit('error', {'message': 'Game not found'})
        return

    game = games[game_id]
    game['current_category'] = category
    game['last_activity'] = datetime.now()

    emit('category_selected', {
        'category': category,
        'game_state': get_game_state(game_id)
    }, room=game_id)

@socketio.on('start_timer')
def handle_start_timer(data):
    game_id = data['game_id']

    if game_id not in games:
        emit('error', {'message': 'Game not found'})
        return

    game = games[game_id]
    game['state'] = 'active_round'
    game['timer_start'] = time.time()
    game['last_activity'] = datetime.now()

    word = get_next_word(game_id)

    emit('timer_started', {
        'word': word,
        'game_state': get_game_state(game_id)
    }, room=game_id)

@socketio.on('correct_guess')
def handle_correct_guess(data):
    game_id = data['game_id']

    if game_id not in games:
        emit('error', {'message': 'Game not found'})
        return

    game = games[game_id]

    if game['state'] != 'active_round':
        return

    time_remaining = game['timer_duration'] - (time.time() - game['timer_start'])
    if time_remaining <= 0:
        return

    game['round_score'] += 1
    game['last_activity'] = datetime.now()

    word = get_next_word(game_id)

    emit('word_changed', {
        'word': word,
        'round_score': game['round_score'],
        'game_state': get_game_state(game_id),
        'action': 'correct'
    }, room=game_id)

@socketio.on('skip_word')
def handle_skip_word(data):
    game_id = data['game_id']

    if game_id not in games:
        emit('error', {'message': 'Game not found'})
        return

    game = games[game_id]

    if game['state'] != 'active_round':
        return

    time_remaining = game['timer_duration'] - (time.time() - game['timer_start'])
    if time_remaining <= 0:
        return

    game['last_activity'] = datetime.now()
    word = get_next_word(game_id)

    emit('word_changed', {
        'word': word,
        'round_score': game['round_score'],
        'game_state': get_game_state(game_id),
        'action': 'skip'
    }, room=game_id)

@socketio.on('end_round')
def handle_end_round(data):
    game_id = data['game_id']

    if game_id not in games:
        emit('error', {'message': 'Game not found'})
        return

    game = games[game_id]

    if game['current_guesser_id']:
        game['players'][game['current_guesser_id']]['score'] += game['round_score']

    game['state'] = 'lobby'
    game['timer_start'] = None
    game['current_word'] = None
    game['last_activity'] = datetime.now()

    emit('round_ended', {
        'final_score': game['round_score'],
        'guesser_id': game['current_guesser_id'],
        'game_state': get_game_state(game_id)
    }, room=game_id)

@socketio.on('disconnect')
def handle_disconnect():
    for game_id, game in games.items():
        for player_id, player in game['players'].items():
            if player.get('sid') == request.sid:
                player['connected'] = False
                emit('player_left', {
                    'player_name': player['name'],
                    'game_state': get_game_state(game_id)
                }, room=game_id)
                break

HTML_TEMPLATE = """
<!DOCTYPE html>
<html>
<head>
    <title>Cranium Charades</title>
    <meta name="viewport" content="width=device-width, initial-scale=1">
    <script src="https://cdn.socket.io/4.5.4/socket.io.min.js"></script>
    <style>
        * {
            margin: 0;
            padding: 0;
            box-sizing: border-box;
        }

        body {
            font-family: -apple-system, BlinkMacSystemFont, 'Segoe UI', Roboto, sans-serif;
            background: linear-gradient(135deg, #667eea 0%, #764ba2 100%);
            min-height: 100vh;
            color: white;
            padding: 20px;
        }

        .container {
            max-width: 600px;
            margin: 0 auto;
        }

        .screen {
            display: none;
            animation: fadeIn 0.3s ease-in;
        }

        .screen.active {
            display: block;
        }

        @keyframes fadeIn {
            from { opacity: 0; transform: translateY(10px); }
            to { opacity: 1; transform: translateY(0); }
        }

        h1 {
            font-size: 2.5em;
            text-align: center;
            margin: 40px 0 20px;
        }

        .emoji {
            text-align: center;
            font-size: 4em;
            margin: 20px 0;
        }

        .card {
            background: rgba(255, 255, 255, 0.15);
            backdrop-filter: blur(10px);
            border-radius: 15px;
            padding: 30px;
            margin: 20px 0;
        }

        button {
            width: 100%;
            padding: 18px;
            font-size: 1.1em;
            font-weight: 600;
            border: none;
            border-radius: 10px;
            cursor: pointer;
            transition: transform 0.2s, box-shadow 0.2s;
            margin: 10px 0;
        }

        button:hover {
            transform: translateY(-2px);
            box-shadow: 0 5px 20px rgba(0,0,0,0.3);
        }

        button:active {
            transform: translateY(0);
        }

        .btn-primary {
            background: linear-gradient(135deg, #667eea 0%, #764ba2 100%);
            color: white;
        }

        .btn-secondary {
            background: rgba(255, 255, 255, 0.9);
            color: #667eea;
        }

        .btn-success {
            background: #10b981;
            color: white;
        }

        .btn-danger {
            background: #ef4444;
            color: white;
        }

        input {
            width: 100%;
            padding: 15px;
            font-size: 1.1em;
            border: none;
            border-radius: 10px;
            margin: 10px 0;
            background: rgba(255, 255, 255, 0.9);
        }

        .players-list {
            list-style: none;
            margin: 20px 0;
        }

        .player-item {
            background: rgba(255, 255, 255, 0.1);
            padding: 15px;
            margin: 10px 0;
            border-radius: 10px;
            display: flex;
            justify-content: space-between;
            align-items: center;
        }

        .player-item.highlight {
            background: rgba(255, 215, 0, 0.3);
            border: 2px solid gold;
        }

        .timer {
            font-size: 3em;
            text-align: center;
            margin: 20px 0;
            font-weight: bold;
        }

        .timer.warning {
            color: #fbbf24;
        }

        .timer.danger {
            color: #ef4444;
            animation: pulse 1s infinite;
        }

        @keyframes pulse {
            0%, 100% { transform: scale(1); }
            50% { transform: scale(1.1); }
        }

        .word-display {
            font-size: 2.5em;
            text-align: center;
            margin: 30px 0;
            padding: 40px;
            background: rgba(255, 255, 255, 0.2);
            border-radius: 15px;
            font-weight: bold;
            min-height: 120px;
            display: flex;
            align-items: center;
            justify-content: center;
        }

        .score {
            font-size: 2em;
            text-align: center;
            margin: 20px 0;
        }

        .game-code {
            text-align: center;
            font-size: 1.3em;
            margin: 20px 0;
            padding: 15px;
            background: rgba(255, 255, 255, 0.2);
            border-radius: 10px;
            font-weight: 600;
        }

        .share-link {
            word-break: break-all;
            background: rgba(255, 255, 255, 0.9);
            color: #667eea;
            padding: 10px;
            border-radius: 5px;
            margin: 10px 0;
            font-size: 0.9em;
        }

        .category-grid {
            display: grid;
            grid-template-columns: 1fr;
            gap: 10px;
            margin: 20px 0;
        }

        @media (min-width: 500px) {
            .category-grid {
                grid-template-columns: 1fr 1fr;
            }
        }

        .waiting-message {
            text-align: center;
            font-size: 1.2em;
            padding: 40px 20px;
        }

        .text-center {
            text-align: center;
        }

        .mb-10 {
            margin-bottom: 10px;
        }

        .mb-20 {
            margin-bottom: 20px;
        }

        .flash-message {
            position: fixed;
            top: 50%;
            left: 50%;
            transform: translate(-50%, -50%);
            font-size: 4em;
            font-weight: bold;
            padding: 40px 60px;
            border-radius: 20px;
            z-index: 1000;
            animation: flashIn 1.2s ease-out;
            pointer-events: none;
        }

        .flash-correct {
            background: linear-gradient(135deg, #10b981 0%, #059669 100%);
            color: white;
            box-shadow: 0 10px 40px rgba(16, 185, 129, 0.5);
        }

        .flash-skip {
            background: linear-gradient(135deg, #f59e0b 0%, #d97706 100%);
            color: white;
            box-shadow: 0 10px 40px rgba(245, 158, 11, 0.5);
            top: 20%;
        }

        @keyframes flashIn {
            0% {
                opacity: 0;
                transform: translate(-50%, -50%) scale(0.5);
            }
            50% {
                opacity: 1;
                transform: translate(-50%, -50%) scale(1.1);
            }
            100% {
                opacity: 0;
                transform: translate(-50%, -50%) scale(1);
            }
        }
    </style>
</head>
<body>
    <div class="container">
        <div id="landing-screen" class="screen active">
            <div class="emoji">🧠</div>
            <h1>Cranium Charades</h1>
            <div class="card">
                <p class="text-center mb-20">Real-time multiplayer word-guessing game for remote teams!</p>
                <button class="btn-primary" onclick="showCreateGame()">Start New Game</button>
                <button class="btn-secondary" onclick="showJoinGame()">Join Game</button>
            </div>
        </div>

        <div id="create-game-screen" class="screen">
            <h1>Create Game</h1>
            <div class="card">
                <p class="text-center mb-20">Creating your game...</p>
                <div id="game-code-display" style="display:none;">
                    <p class="text-center mb-10">Game Code:</p>
                    <div class="game-code" id="game-code"></div>
                    <p class="text-center mb-10">Share this link:</p>
                    <div class="share-link" id="share-link"></div>
                    <button class="btn-primary" onclick="copyShareLink()">Copy Link</button>
                    <div style="margin-top: 20px;">
                        <input type="text" id="creator-name" placeholder="Enter your name">
                        <button class="btn-success" onclick="joinAsCreator()">Join Game</button>
                    </div>
                </div>
            </div>
        </div>

        <div id="join-game-screen" class="screen">
            <h1>Join Game</h1>
            <div class="card">
                <input type="text" id="join-game-code" placeholder="Enter game code">
                <input type="text" id="join-player-name" placeholder="Enter your name">
                <button class="btn-primary" onclick="joinGame()">Join</button>
                <button class="btn-secondary" onclick="showLanding()">Back</button>
            </div>
        </div>

        <div id="lobby-screen" class="screen">
            <h1>Game Lobby</h1>
            <div class="card">
                <div class="game-code" id="lobby-game-code"></div>
                <h2 class="text-center mb-20">Players</h2>
                <ul class="players-list" id="lobby-players"></ul>
                <button class="btn-primary" onclick="startRound()">It's my turn!</button>
            </div>
        </div>

        <div id="category-selection-screen" class="screen">
            <h1>Choose Category</h1>
            <div class="card">
                <p class="text-center mb-20" id="category-message"></p>
                <div id="category-grid" class="category-grid"></div>
                <div id="category-waiting" class="waiting-message" style="display:none;">
                    Waiting for category selection...
                </div>
            </div>
        </div>

        <div id="ready-screen" class="screen">
            <h1>Ready?</h1>
            <div class="card">
                <p class="text-center mb-20">Category: <strong id="ready-category"></strong></p>
                <p class="text-center mb-20" id="ready-message"></p>
                <button class="btn-success" onclick="startTimer()" id="start-button">Start!</button>
                <div id="ready-waiting" class="waiting-message" style="display:none;">
                    Waiting for guesser to start...
                </div>
            </div>
        </div>

        <div id="active-round-guesser-screen" class="screen">
            <h1>Guess the Word!</h1>
            <div class="card">
                <div class="timer" id="guesser-timer">60</div>
                <div class="score">Score: <span id="guesser-score">0</span></div>
                <p class="text-center">Listen to your teammates' hints!</p>
                <button class="btn-danger" onclick="skipWord()">Skip</button>
            </div>
        </div>

        <div id="active-round-hinter-screen" class="screen">
            <h1>Give Hints!</h1>
            <div class="card">
                <div class="timer" id="hinter-timer">60</div>
                <div class="word-display" id="hinter-word"></div>
                <div class="score">Guesser Score: <span id="hinter-score">0</span></div>
                <button class="btn-success" onclick="correctGuess()">Got it!</button>
            </div>
        </div>
    </div>

    <script>
        const socket = io();
        let currentGameId = null;
        let currentPlayerId = null;
        let isGuesser = false;
        let timerInterval = null;

        function showScreen(screenId) {
            document.querySelectorAll('.screen').forEach(s => s.classList.remove('active'));
            document.getElementById(screenId).classList.add('active');
        }

        function showLanding() {
            showScreen('landing-screen');
        }

        function showCreateGame() {
            showScreen('create-game-screen');
            socket.emit('create_game');
        }

        function showJoinGame() {
            const path = window.location.pathname;
            if (path.startsWith('/game/')) {
                const gameCode = path.split('/game/')[1];
                document.getElementById('join-game-code').value = gameCode;
            }
            showScreen('join-game-screen');
        }

        function copyShareLink() {
            const link = document.getElementById('share-link').textContent;
            navigator.clipboard.writeText(link);
            alert('Link copied to clipboard!');
        }

        function joinAsCreator() {
            const name = document.getElementById('creator-name').value.trim();
            if (!name) {
                alert('Please enter your name');
                return;
            }
            socket.emit('join_game', {
                game_id: currentGameId,
                player_name: name
            });
        }

        function joinGame() {
            const gameCode = document.getElementById('join-game-code').value.trim();
            const playerName = document.getElementById('join-player-name').value.trim();

            if (!gameCode || !playerName) {
                alert('Please enter both game code and your name');
                return;
            }

            currentGameId = gameCode;
            socket.emit('join_game', {
                game_id: gameCode,
                player_name: playerName
            });
        }

        function startRound() {
            socket.emit('start_round', {
                game_id: currentGameId,
                player_id: currentPlayerId
            });
        }

        function selectCategory(category) {
            socket.emit('select_category', {
                game_id: currentGameId,
                category: category
            });
        }

        function startTimer() {
            socket.emit('start_timer', {
                game_id: currentGameId
            });
        }

        function correctGuess() {
            socket.emit('correct_guess', {
                game_id: currentGameId
            });
        }

        function skipWord() {
            socket.emit('skip_word', {
                game_id: currentGameId
            });
        }

        function updateTimer(timeRemaining) {
            const seconds = Math.ceil(timeRemaining);
            const timerElements = document.querySelectorAll('.timer');

            timerElements.forEach(el => {
                el.textContent = seconds;
                el.classList.remove('warning', 'danger');
                if (seconds <= 10) el.classList.add('danger');
                else if (seconds <= 20) el.classList.add('warning');
            });

            if (timeRemaining <= 0) {
                if (timerInterval) clearInterval(timerInterval);
                socket.emit('end_round', { game_id: currentGameId });
            }
        }

        function showFlash(message, type) {
            const flash = document.createElement('div');
            flash.className = `flash-message flash-${type}`;
            flash.textContent = message;
            document.body.appendChild(flash);

            setTimeout(() => {
                flash.remove();
            }, 1200);
        }

        function renderLobby(gameState) {
            document.getElementById('lobby-game-code').textContent = gameState.game_id;

            const playersList = document.getElementById('lobby-players');
            playersList.innerHTML = '';

            gameState.players.forEach(player => {
                const li = document.createElement('li');
                li.className = 'player-item';
                li.innerHTML = `
                    <span>${player.name}${player.connected ? '' : ' (disconnected)'}</span>
                    <span>Score: ${player.score}</span>
                `;
                playersList.appendChild(li);
            });

            showScreen('lobby-screen');
        }

        socket.on('game_created', (data) => {
            currentGameId = data.game_id;
            const shareUrl = `${window.location.origin}/game/${data.game_id}`;

            document.getElementById('game-code').textContent = data.game_id;
            document.getElementById('share-link').textContent = shareUrl;
            document.getElementById('game-code-display').style.display = 'block';
        });

        socket.on('joined_game', (data) => {
            currentPlayerId = data.player_id;
            currentGameId = data.game_state.game_id;
            renderLobby(data.game_state);
        });

        socket.on('player_joined', (data) => {
            if (data.game_state.state === 'lobby') {
                renderLobby(data.game_state);
            }
        });

        socket.on('round_started', (data) => {
            isGuesser = (data.game_state.current_guesser_id === currentPlayerId);

            if (isGuesser) {
                document.getElementById('category-message').textContent = 'Choose a category:';
                const grid = document.getElementById('category-grid');
                grid.innerHTML = '';

                data.game_state.categories.forEach(cat => {
                    const btn = document.createElement('button');
                    btn.className = 'btn-primary';
                    btn.textContent = cat;
                    btn.onclick = () => selectCategory(cat);
                    grid.appendChild(btn);
                });

                document.getElementById('category-grid').style.display = 'grid';
                document.getElementById('category-waiting').style.display = 'none';
            } else {
                document.getElementById('category-message').textContent = `${data.guesser_name} is choosing a category...`;
                document.getElementById('category-grid').style.display = 'none';
                document.getElementById('category-waiting').style.display = 'block';
            }

            showScreen('category-selection-screen');
        });

        socket.on('category_selected', (data) => {
            document.getElementById('ready-category').textContent = data.category;

            if (isGuesser) {
                document.getElementById('ready-message').textContent = "Click Start when you're ready!";
                document.getElementById('start-button').style.display = 'block';
                document.getElementById('ready-waiting').style.display = 'none';
            } else {
                document.getElementById('ready-message').textContent = 'Get ready to give hints!';
                document.getElementById('start-button').style.display = 'none';
                document.getElementById('ready-waiting').style.display = 'block';
            }

            showScreen('ready-screen');
        });

        socket.on('timer_started', (data) => {
            if (isGuesser) {
                document.getElementById('guesser-score').textContent = '0';
                document.getElementById('guesser-timer').textContent = '60';
                showScreen('active-round-guesser-screen');
            } else {
                document.getElementById('hinter-word').textContent = data.word;
                document.getElementById('hinter-score').textContent = '0';
                document.getElementById('hinter-timer').textContent = '60';
                showScreen('active-round-hinter-screen');
            }

            if (timerInterval) clearInterval(timerInterval);
            const startTime = Date.now();
            timerInterval = setInterval(() => {
                const elapsed = (Date.now() - startTime) / 1000;
                updateTimer(60 - elapsed);
            }, 100);
        });

        socket.on('word_changed', (data) => {
            if (data.action === 'correct') {
                if (isGuesser) {
                    showFlash('✓ CORRECT!', 'correct');
                }
            } else if (data.action === 'skip') {
                if (!isGuesser) {
                    showFlash('SKIPPED', 'skip');
                }
            }

            if (!isGuesser) {
                document.getElementById('hinter-word').textContent = data.word;
            }
            document.getElementById('guesser-score').textContent = data.round_score;
            document.getElementById('hinter-score').textContent = data.round_score;
        });

        socket.on('round_ended', (data) => {
            if (timerInterval) {
                clearInterval(timerInterval);
                timerInterval = null;
            }
            renderLobby(data.game_state);
        });

        socket.on('error', (data) => {
            alert(data.message);
        });

        if (window.location.pathname.startsWith('/game/')) {
            showJoinGame();
        }
    </script>
</body>
</html>
"""

if __name__ == '__main__':
    socketio.run(app, host='127.0.0.1', port=8004, debug=True, allow_unsafe_werkzeug=True)
