import ast
import operator
import os
import re
import subprocess
import tempfile


def _browser_executable():
    import shutil
    env = os.environ.get("BROWSER_BIN") or os.environ.get("CHROME_BIN")
    if env and os.path.exists(env):
        return env
    candidates = [
        r"C:\Program Files (x86)\Microsoft\Edge\Application\msedge.exe",
        r"C:\Program Files\Microsoft\Edge\Application\msedge.exe",
        r"C:\Program Files\Google\Chrome\Application\chrome.exe",
        r"C:\Program Files (x86)\Google\Chrome\Application\chrome.exe",
    ]
    for c in candidates:
        if os.path.exists(c):
            return c
    for name in ("msedge", "chrome", "chromium", "chromium-browser"):
        p = shutil.which(name)
        if p:
            return p
    return None


# Upper bounds for the browser/runtime checks. subprocess.run returns as
# soon as the process exits; it does not wait the full timeout when the
# check finishes early. Override with HOMEBENCH_*_TIMEOUT.
BROWSER_TIMEOUT = int(os.environ.get("HOMEBENCH_BROWSER_TIMEOUT", "30"))
JS_CHECK_TIMEOUT = int(os.environ.get("HOMEBENCH_JS_CHECK_TIMEOUT", "10"))


def _inject_runtime_checks(html):
    capture = ("<script>window.__errors=[];window.__bench_interaction=null;"
               "window.__bench_refresh_status=function(){var d=document.getElementById('__bench_status');"
               "if(d)d.textContent=window.__errors.length?'ERROR: '+window.__errors.join('; '):"
               "window.__bench_interaction===true?'OK':'ERROR: no observable game-state change after interaction';};"
               "window.addEventListener('error',function(e){window.__errors.push(e.message||String(e));"
               "window.__bench_refresh_status();});"
               "window.addEventListener('unhandledrejection',function(e){"
               "window.__errors.push('Promise: '+(e.reason&&(e.reason.message||e.reason)||e.reason));"
               "window.__bench_refresh_status();});"
               "</script>")
    interact = ("<script>window.addEventListener('load',function(){"
                "setTimeout(function(){try{"
                "function snapshot(){var s={dom:document.body?document.body.innerHTML:'',canvas:[]};"
                "Array.from(document.querySelectorAll('canvas')).forEach(function(c){"
                "try{s.canvas.push(c.toDataURL());}catch(e){s.canvas.push(c.width+'x'+c.height);}});"
                "return s;}"
                "function changed(a,b){return JSON.stringify(a)!==JSON.stringify(b);}"
                "var before=snapshot();"
                "setTimeout(function(){var idle=snapshot();"
                "var idleDomChanged=before.dom!==idle.dom;"
                "var idleCanvasChanged=changed(before.canvas,idle.canvas);"
                "var bs=Array.from(document.querySelectorAll('button'));"
                "var play=bs.find(function(b){return /play/i.test(b.textContent||'');});"
                "if(play)play.click();"
                "var c=document.querySelector('canvas');"
                "if(c){var ev=new MouseEvent('mousemove',{clientX:120,clientY:120,bubbles:true});c.dispatchEvent(ev);}"
                "setTimeout(function(){var after=snapshot();"
                "window.__bench_interaction=(!idleDomChanged&&after.dom!==idle.dom)||"
                "(!idleCanvasChanged&&changed(idle.canvas,after.canvas));"
                "window.__bench_refresh_status();},500);"
                "},500);"
                "}catch(e){window.__errors.push('interact: '+(e.message||e));"
                "window.__bench_interaction=false;window.__bench_refresh_status();}"
                "},1000);});</script>")
    status = ("<script>window.addEventListener('load',function(){"
              "setTimeout(function(){var d=document.createElement('div');d.id='__bench_status';"
              "document.body.appendChild(d);window.__bench_refresh_status();},4000);});</script>")
    if re.search(r"<head[^>]*>", html, re.I):
        html = re.sub(r"(<head[^>]*>)", r"\1" + capture, html, count=1, flags=re.I)
    elif re.search(r"<body[^>]*>", html, re.I):
        html = re.sub(r"(<body[^>]*>)", capture + r"\1", html, count=1, flags=re.I)
    else:
        html = capture + html
    if re.search(r"</body>", html, re.I):
        html = re.sub(r"</body>", interact + status + "</body>", html, count=1, flags=re.I)
    else:
        html = html + interact + status
    return html


def _game_runtime_status(html):
    browser = _browser_executable()
    if not browser:
        return None, "runtime check skipped (no browser found)"
    injected = _inject_runtime_checks(html)
    fd, path = tempfile.mkstemp(suffix=".html")
    try:
        with os.fdopen(fd, "w", encoding="utf-8") as f:
            f.write(injected)
        url = "file:///" + path.replace("\\", "/")
        try:
            r = subprocess.run(
                [browser, "--headless=new", "--disable-gpu",
                 "--virtual-time-budget=6000", "--dump-dom", url],
                capture_output=True, text=True, encoding="utf-8", errors="replace",
                timeout=BROWSER_TIMEOUT)
        except subprocess.TimeoutExpired:
            return False, "FAIL: runtime check timed out"
        out = r.stdout or ""
        mm = re.search(r'<div[^>]*id="__bench_status"[^>]*>(.*?)</div>',
                       out, re.S | re.I)
        if not mm:
            if "Uncaught" in out or "ERROR:" in out:
                return False, "FAIL: runtime error detected"
            return None, "runtime check inconclusive (no status)"
        status = mm.group(1).strip()
        if status.startswith("ERROR:"):
            msg = status[len("ERROR:"):].strip()
            return False, "FAIL: runtime error: " + (msg or "unknown")
        return True, "PASS: runs without runtime errors"
    except Exception as e:
        return None, "runtime check skipped (%s)" % e
    finally:
        try:
            os.remove(path)
        except OSError:
            pass


def _game_status(text):
    if not isinstance(text, str):
        return False, "FAIL: no model output received"
    html = _extract_html(text)
    low = html.lower()

    if "<html" not in low and "<!doctype" not in low and "<canvas" not in low:
        return False, "FAIL: not an HTML document"

    for token in ("canvas", "car", "coin", "yellow", "red", "green", "grass",
                  "play", "200"):
        if token not in low:
            return False, "FAIL: missing required element/content '%s'" % token

    if not any(s in low for s in ("audiocontext", "oscillator", "audio", "sound",
                                  "beep", "tone", "webaudio")):
        return False, "FAIL: no generated sound (audio) found"

    if not any(s in low for s in ("mousemove", "touchmove", "pointermove",
                                  "mousedown", "touchstart", "pointerdown")):
        return False, "FAIL: no mouse/touch input handler found"

    if not any(s in low for s in ("spawn", "setinterval", "settimeout")):
        return False, "FAIL: no coin spawning logic found"

    if re.search(r"<script[^>]*\bsrc\s*=", html, re.I):
        return False, "FAIL: uses external script (src=) - not a single file"

    scripts = re.findall(r"<script[^>]*>(.*?)</script>", html, re.S | re.I)
    js = "\n".join(scripts)
    if js.strip():
        fd, path = tempfile.mkstemp(suffix=".js")
        try:
            with os.fdopen(fd, "w") as f:
                f.write(js)
            r = subprocess.run(["node", "--check", path], capture_output=True,
                               timeout=JS_CHECK_TIMEOUT)
            if r.returncode != 0:
                err = (r.stderr or b"").decode(errors="replace").strip()
                msg = err.splitlines()[-1] if err else "syntax error"
                return False, "FAIL: JS syntax error: " + msg
        except Exception as e:
            return False, "FAIL: could not check JS (%s)" % e
        finally:
            try:
                os.remove(path)
            except OSError:
                pass

    coins_ok, coins_reason = _coin_bounds_and_collection_status(js)
    if not coins_ok:
        return False, coins_reason

    rt_ok, rt_reason = _game_runtime_status(html)
    if rt_ok is False:
        return False, rt_reason
    if rt_ok is None:
        return False, "INCONCLUSIVE: " + rt_reason
    return True, ("PASS: valid single-file HTML game with all required elements; "
                  "coins render inside the canvas and are collectible (runtime OK)")


def _coin_bounds_and_collection_status(js):
    operators = {
        ast.Add: operator.add,
        ast.Sub: operator.sub,
        ast.Mult: operator.mul,
        ast.Div: operator.truediv,
    }

    def interval(node, dimension, radius):
        if isinstance(node, ast.Expression):
            return interval(node.body, dimension, radius)
        if isinstance(node, ast.Constant) and isinstance(node.value, (int, float)):
            return node.value, node.value
        if isinstance(node, ast.Name):
            return {
                "random": (0.0, 1.0),
                "dimension": (dimension, dimension),
                "radius": (radius, radius),
            }.get(node.id)
        if isinstance(node, ast.BinOp) and type(node.op) in operators:
            left = interval(node.left, dimension, radius)
            right = interval(node.right, dimension, radius)
            if left is None or right is None:
                return None
            fn = operators[type(node.op)]
            if isinstance(node.op, ast.Add):
                return left[0] + right[0], left[1] + right[1]
            if isinstance(node.op, ast.Sub):
                return left[0] - right[1], left[1] - right[0]
            if isinstance(node.op, ast.Mult):
                values = [fn(a, b) for a in left for b in right]
                return min(values), max(values)
            if 0 in right:
                return None
            values = [fn(a, b) for a in left for b in right]
            return min(values), max(values)
        return None

    def bounded_coin_axis(axis, dimension_name):
        coin_objects = re.finditer(
            r"\b(?:const|let|var)\s+[\w$]*coin[\w$]*\s*=\s*\{([^{}]*)\}",
            js, re.I | re.S)
        for match in coin_objects:
            body = match.group(1)
            radius_match = re.search(
                r"\bradius\s*:\s*(\d+(?:\.\d+)?)\b", body, re.I)
            position_match = re.search(
                r"\b" + axis + r"\s*:\s*([^,}]+)", body, re.I | re.S)
            if not radius_match or not position_match:
                continue
            radius = float(radius_match.group(1))
            expression = position_match.group(1).strip()
            if not re.search(r"\bMath\.random\s*\(", expression, re.I):
                continue
            expression = re.sub(r"\bMath\.random\s*\(\s*\)", "random",
                                expression, flags=re.I)
            expression = re.sub(r"\bcanvas\s*\.\s*" + dimension_name,
                                "dimension", expression, flags=re.I)
            expression = re.sub(r"\b(?:coin|newCoin)\s*\.\s*radius",
                                "radius", expression, flags=re.I)
            try:
                parsed = ast.parse(expression, mode="eval")
            except SyntaxError:
                continue
            size = 1000000.0
            bounds = interval(parsed, size, radius)
            if bounds and bounds[0] >= radius and bounds[1] <= size - radius:
                return True
        return False

    if not (bounded_coin_axis("x", "width")
            and bounded_coin_axis("y", "height")):
        return False, ("FAIL: coins must spawn with an inset from all canvas "
                       "edges so each coin renders fully inside the canvas")

    collection_path = False
    for match in re.finditer(
            r"\bif\s*\(([\s\S]*?)\)\s*\{([\s\S]*?)\}", js, re.I):
        condition, body = match.groups()
        has_player = re.search(r"\b(?:car|player)\b", condition, re.I)
        has_coin = re.search(r"\bcoin\w*\b", condition, re.I)
        has_collision = re.search(
            r"\b(?:collision\w*|distance\w*|hypot|overlap\w*|"
            r"intersect\w*)\b|math\.abs\s*\(|[<>]=?|!==|===",
            condition, re.I)
        removes_coin = re.search(
            r"\bcoins?\s*\.\s*(?:splice|pop|filter)\s*\(|"
            r"\b(?:remove|delete)\s*\(\s*coin\w*\b", body, re.I)
        updates_score = re.search(
            r"\bscore\b\s*(?:\+\+|--|[+\-]?=)", body, re.I)
        if (has_player and has_coin and has_collision
                and (removes_coin or updates_score)):
            collection_path = True
            break
    if not collection_path:
        return False, ("FAIL: coins must be checked for collision with the "
                       "car/player and removed or counted when collected")
    return True, "PASS: coins render inside the canvas and are collectible"


def _extract_html(text):
    fences = re.finditer(
        r"(?im)^[ \t]{0,3}```[ \t]*(html|htm)?[ \t]*\r?\n"
        r"(.*?)(?:^[ \t]{0,3}```[ \t]*\r?$|\Z)",
        text, re.S | re.M)
    blocks = [(m.group(1), m.group(2).strip()) for m in fences]
    for language, content in blocks:
        if language or re.search(r"(?i)<!doctype\s+html|<html[\s>]", content):
            return content

    start = re.search(r"(?i)<!doctype\s+html|<html[\s>]", text)
    if start:
        return text[start.start():].strip()
    return text.strip()


def check(text):
    return _game_status(text)[0]


def explain(text):
    return _game_status(text)[1]


PROMPT = (
    "Create a single-file HTML5 game for a 3-year-old toddler following this design document exactly:\n\n"
    "Generate a 2d game for my 3 year old toddler.\n\n"
    "The gameplay is as follows:\n"
    "1. you use the mouse or touch to move a car on the screen.\n"
    "2. there are Yellow coins spawning every 1 to 2 seconds.\n"
    "3. maximum number of yellow coins on the screen at any given time is 5.\n"
    "3a. if you collect the yellow coins faster than the spawning speed, then the spawning speed decreases to 0.3 to 0.8 sec. to allow for faster yellow coins appearing on the screen.\n"
    "4. after 5 to 10 yellow (random number each time 5-10) coins are collected a Red coin appears.\n"
    "4a. every next red coin should appear after 5 to 10 (random 5-10) yellow coins are collected.\n"
    "5. after 2 red coins are collected a cluster of 5 Green coins appears.\n\n"
    "Win condition:\n"
    "After 200 total coins are collected the game ends.\n\n"
    "Constraints:\n"
    "Single HTML File (index.html)\n\n"
    "State:\n"
    "Main menu with a single play button which starts the game.\n\n"
    "Visual style:\n"
    "Bright and cartoony style, bright colors. Grass. Flags.\n\n"
    "Sound:\n"
    "Generated sounds for coin pickup.\n"
    "Different sound for the different color coins.\n\n"
    "Requirements:\n"
    "- Output ONLY the complete index.html inside a single ```html code block.\n"
    "- The file must be fully self-contained (inline CSS and JS, no external dependencies or CDN links).\n"
    "- Implement every gameplay rule, the win condition, the main menu, the visual style, and the generated sounds."
)

ID = "game"
