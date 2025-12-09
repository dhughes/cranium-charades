# Cranium Charades - Game Requirements

## Overview

Cranium Charades is a real-time multiplayer word-guessing game designed for remote teams to play during Zoom meetings or voice calls. Players take turns guessing words/phrases while their teammates give hints, racing against a 1-minute timer to score as many points as possible. No screen sharing required - each player views the game in their own browser.

## Technical Constraints

- **No database**: All game state stored in-memory on the server
- **Real-time communication**: WebSockets for instant updates to all players
- **Stateless rooms**: Game state persists only while server is running
- **Drop-in/drop-out**: Players can join mid-game or leave at any time
- **Categories and words**: Loaded from JSON file with starter content included

## Game Flow

### 1. Landing Page

When a user first visits the app, they see two options:

- **Start a new game**: Creates a new game with a unique 3-word identifier (e.g., "running-blue-squash")
- **Join a game**: Prompts for a game code to join an existing game

### 2. Game Creation

When someone starts a new game:
1. Server generates a unique 3-word game code
2. User is shown the game code and a shareable link (e.g., `https://www.doughughes.net/cranium-charades/game/running-blue-squash`)
3. User can copy the link to share with teammates via Zoom chat or other means
4. Creator proceeds to join the game like any other player

### 3. Joining a Game

When joining a game (via link or entering code):
1. Player enters their display name
2. Player joins the game lobby
3. Player can join even if a round is in progress (they become a hinter for the current round)

### 4. Game Lobby

The lobby is where players wait between rounds:

**Display:**
- List of all connected players
- Current scoreboard (player names and points)
- Previous round's guesser highlighted with their score
- Large "It's my turn!" button

**Actions:**
- Any player can click "It's my turn!" to become the guesser and start a new round
- No concept of "host" - anyone can start a round at any time

### 5. Starting a Round

When a player clicks "It's my turn!":
1. That player becomes the **guesser** for this round
2. All other players become **hinters**
3. Guesser sees a list of available categories
4. Hinters see a waiting room message (e.g., "Waiting for [Player Name] to choose a category...")

### 6. Category Selection

**Starter Categories:**
- Movies
- Famous People
- Animals
- Foods
- Actions/Activities
- Objects
- Travel and Landmarks

The guesser picks one category, and it's immediately shown to all hinters.

### 7. Active Round Gameplay

Once the guesser is ready, they click a "Start" button, which:
1. Starts a **60-second countdown timer** (visible to all players)
2. Shows the first word/phrase to all **hinters only**
3. Hinters begin shouting hints over the call
4. Guesser tries to guess the word

**Guesser's View:**
- Countdown timer
- Current score for this round
- "Skip" button to skip the current word

**Hinters' View:**
- Countdown timer
- Current word/phrase being hinted
- "Got it!" button to click when guesser says the correct word
- Current guesser's score for this round

### 8. Scoring

When the guesser says the correct word:
1. One or more hinters click the "Got it!" button
2. System registers ONE point for the guesser (even if multiple hinters click simultaneously)
3. Next word/phrase immediately shows to hinters
4. Timer continues counting down
5. Repeat until timer expires

**Skip Functionality:**
- Guesser can click "Skip" at any time
- No points awarded for skipped words
- Next word immediately shows to hinters
- Skipped words don't come back in the same round

### 9. Round End

When the 60-second timer expires:
1. Current word is hidden
2. Final score for the round is shown to all players
3. All players automatically return to the lobby
4. Scoreboard updates to show all players' total points
5. Previous guesser's score is highlighted/emphasized
6. Players can start a new round by clicking "It's my turn!"

### 10. Ongoing Play

- Game continues indefinitely until players decide to stop
- No formal "end game" state - players simply close the browser when done
- Scores persist for the duration of the game session
- If server restarts, all game state is lost

## Game State Data Model

### Game Object
```python
{
  "game_id": "running-blue-squash",
  "players": [
    {"player_id": "abc123", "name": "Alice", "score": 15, "connected": True},
    {"player_id": "def456", "name": "Bob", "score": 12, "connected": True}
  ],
  "state": "lobby" | "category_selection" | "active_round" | "round_end",
  "current_guesser_id": None | "abc123",
  "current_category": None | "Movies",
  "current_word": None | "The Matrix",
  "round_score": 0,
  "timer_start": None | timestamp,
  "timer_duration": 60,
  "words_used_this_round": ["The Matrix", "Inception"]
}
```

### Words JSON Structure
```json
{
  "Movies": [
    "The Matrix",
    "Inception",
    "Titanic",
    ...
  ],
  "Famous People": [
    "Albert Einstein",
    "Beyoncé",
    ...
  ],
  "Animals": [...],
  "Foods": [...],
  "Actions/Activities": [...],
  "Objects": [...],
  "Travel and Landmarks": [...]
}
```

## WebSocket Events

### Client → Server
- `join_game`: Player joins a game (includes name)
- `start_round`: Player volunteers to be guesser
- `select_category`: Guesser picks a category
- `start_timer`: Guesser starts the round
- `correct_guess`: Hinter clicks "Got it!"
- `skip_word`: Guesser skips current word
- `disconnect`: Player leaves (automatic)

### Server → Client
- `game_state`: Full game state update
- `player_joined`: New player joined
- `player_left`: Player disconnected
- `round_started`: Round began, show category selection
- `category_selected`: Category chosen, show to hinters
- `timer_started`: Timer started, show word to hinters
- `word_changed`: New word to hint
- `round_ended`: Timer expired, return to lobby
- `score_updated`: Scoreboard changed

## Technical Implementation Notes

### Word/Phrase Storage
- Categories and words stored in `words.json` file
- Loaded into memory on server startup
- Each category contains 50+ words/phrases in the starter set
- Random selection within category, excluding already-used words in current round
- Assumption: Enough words exist that we won't run out during a 60-second round

### Simultaneous "Got it!" Clicks
- Server maintains a lock/flag per game
- First "correct_guess" event processed scores the point
- Subsequent simultaneous events within ~100ms window are ignored
- Alternative: Use timestamp to determine first click

### Player Connection Handling
- Player disconnects: Mark as `connected: False`, keep in player list
- Player reconnects with same name: Resume their position and score
- Player abandons game: Eventually garbage collect after X hours of inactivity

### Game Cleanup
- Games with zero connected players for >1 hour can be deleted
- Simple periodic cleanup task runs every 15-30 minutes

## UI/UX Considerations

### Responsive Design
- Mobile-responsive layout using modern CSS (flexbox/grid)
- Works well on desktop browsers (primary use case)
- Also works on mobile phones and tablets
- Touch-friendly buttons with adequate sizing
- Readable fonts at various screen sizes

### Visual Hierarchy

**Lobby:**
- "It's my turn!" button is the primary action
- Scoreboard clearly shows current standings

**Active Round (Guesser):**
- Timer is primary focus
- "Skip" button is secondary action

**Active Round (Hinter):**
- Current word/phrase is primary focus (large, prominent display)
- Timer secondary
- "Got it!" button prominent
- Guesser's current round score visible

### Accessibility
- High contrast for readability during video calls
- Clear state transitions
- Obvious visual feedback for all actions
- Works over voice-only calls (no video/screen sharing required)

## Starter Content

The initial `words.json` file should include 7 categories with 50+ words/phrases each:

1. **Movies**: Popular films across decades
2. **Famous People**: Historical figures, celebrities, athletes
3. **Animals**: Common and exotic animals
4. **Foods**: Dishes, ingredients, cuisines
5. **Actions/Activities**: Verbs and activities (e.g., "Swimming", "Painting a fence")
6. **Objects**: Everyday items and objects
7. **Travel and Landmarks**: Famous places, monuments, cities
