from tasks import game


def _solved_status(text):
    return game._game_status(text)


def check(text):
    return _solved_status(text)[0]


def explain(text):
    return _solved_status(text)[1]


# Master prompt that contains everything needed to pass the game test
PROMPT = game.PROMPT + """

ADDITIONAL MANDATORY IMPLEMENTATION REQUIREMENTS (to pass all tests):
- You MUST output ONLY a complete, single-file index.html wrapped in `html` code block
- Include inline <style> with bright cartoony colors, grass background/terrain, flags/decorations
- Include a main menu with a single "Play" button (or button containing "Play") that starts the game
- Create a car/player object that moves with mousemove/touchmove/pointermove OR mousedown/touchstart/pointerdown controls
- Spawn Yellow coins every 1 to 2 seconds (random interval 1000-2000ms). Max 5 yellow coins on screen at a time.
- When collecting yellow coins faster than spawning allows, decrease spawn interval to 0.3-0.8 seconds to spawn faster
- After collecting 5 to 10 yellow coins (random each cycle, 5-10), spawn a Red coin
- After collecting 2 red coins total, spawn a cluster of 5 Green coins
- Track total coins collected; game ends when total collected >= 200
- Spawn every coin with enough inset from all four canvas edges for the whole coin to remain visible, and implement collision detection so the car/player can collect every coin
- Generate sounds for coin pickup using Web Audio API (AudioContext/oscillator) with different sounds for yellow, red, green coins
- Use setInterval/setTimeout for spawning logic
- All JavaScript inline in <script> tags (no external src scripts)
- Valid JavaScript syntax
- Must be playable with observable game state changes on interaction (click Play, move mouse)
- No runtime errors
- Write all JavaScript in pure ASCII only: do NOT include any emoji or non-ASCII Unicode glyphs anywhere in the .js code or inline strings. Use only ASCII letters, digits, punctuation, and standard whitespace.
- For any special character that must appear (ampersand, arrow, bullet, symbol, etc.), use either an HTML entity (e.g. &amp; for &, &lt; for <) or a JavaScript Unicode escape sequence (e.g. \u0026 for &, \u2192 for →, \u2022 for •, \u2665 for ♥, \u2605 for ★) so the emitted code contains no raw high bytes.
- Never emit raw UTF-8 or UTF-16 non-ASCII bytes in the JavaScript source; every non-ASCII character must be represented as a escape inside string literals.
- If you need a visual symbol in the HTML/CSS, use an HTML entity, ANSI/ASCII art, CSS borders, or an inline SVG, never an emoji character.
- The entire file must be safely written and read on Windows with the default 'charmap' (ANSI) encoding without a "character maps to <undefined>" error.
- Include canvas element for rendering
"""
ID = "game_solved"
