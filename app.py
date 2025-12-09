#!/usr/bin/env python3
"""
Cranium Charades - Forehead word guessing game
"""
from flask import Flask, render_template_string

app = Flask(__name__)

HTML_TEMPLATE = """
<!DOCTYPE html>
<html>
<head>
    <title>Cranium Charades</title>
    <meta name="viewport" content="width=device-width, initial-scale=1">
    <style>
        body {
            font-family: -apple-system, BlinkMacSystemFont, 'Segoe UI', Roboto, sans-serif;
            max-width: 800px;
            margin: 0 auto;
            padding: 40px 20px;
            text-align: center;
            background: linear-gradient(135deg, #667eea 0%, #764ba2 100%);
            min-height: 100vh;
            color: white;
        }
        h1 {
            font-size: 3em;
            margin-bottom: 0.2em;
        }
        .emoji {
            font-size: 5em;
            margin: 20px 0;
        }
        p {
            font-size: 1.2em;
            line-height: 1.6;
        }
        .coming-soon {
            background: rgba(255, 255, 255, 0.2);
            padding: 20px;
            border-radius: 10px;
            margin-top: 40px;
        }
    </style>
</head>
<body>
    <div class="emoji">🧠</div>
    <h1>Cranium Charades</h1>
    <p>The forehead word guessing game!</p>
    <div class="coming-soon">
        <h2>Coming Soon!</h2>
        <p>Get ready to hold your phone to your forehead and guess words from your friends' clues.</p>
    </div>
</body>
</html>
"""

@app.route('/')
def index():
    return render_template_string(HTML_TEMPLATE)

if __name__ == '__main__':
    app.run(host='127.0.0.1', port=8004, debug=True)
