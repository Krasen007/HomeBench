i want to create a new benchmark to test llm models
tell me what tools i need to create it?
can it be super simple with just 5 tasks for example, its just a demo to test few simple models.

i will use llama.cpp with small local models

in @/mini_bench.py implement F:\AI\repos\HomeBench\GameDesignDocument.md as a test in the suite of tasks

make the web interface render correctly markdown

for each pass or fail show the passing or failing condition in the answer

when i run the same model multiple times Model name (label for the table) should not replace the last results, add automatic increments, also it should be possible to infer the name of the model from llama.cpp

one of the current tasks is to create a single html application, i want to be able to view the resulting html from the results of the task, maybe add a button to show in external page or render it inside the current page

in the game task, there should be more checks that detirmine if its a pass, the game should not throw errors and be playable

i have made it to show pages for every run, also can you move the next prev buttons at the top, also move the render inline and open html in new tab above the code

add another task to check bulgarian 
Грешно използван пълен член (когато трябва да е кратък)
Пълен член се използва само ако думата е подлог (вършител на действието) или сказуемно определение. Ако върху думата се извършва действието, се използва кратък член.
Грешно: Вчера видях директорът. ❌
Правилно: Вчера видях директора. (Аз го видях, той е допълнение).
Грешно: Отидохме при лекарят. ❌
Правилно: Отидохме при лекаря. (След предлози като при, в, на, с, за винаги се използва кратък член).
Грешно: Извикаха ученикът в кабинета. ❌
Правилно: Извикаха ученика в кабинета.

extract all tasks and checks into separate files into a new folder

there is a bug, when i try to view some of the results in the web view the results show for a moment and then hide, this happens when the benchmark is running, however i want to be able to view the results in real time
make the button Render HTML inline , actually show the render above the answer, e.g. below the button.

### 3. Improve the empty state (Low priority)
__Action:__ Replace `"No results yet. Run a model above."` with something more welcoming — e.g., show the 7 task IDs with brief descriptions so a new user knows what will be tested.
### 4. Add a security warning for `code_task` (Medium priority)
__Action:__ Add a clear, visible warning in both CLI and web UI that model-generated code is executed locally. Consider sandboxing options.

extract the html from web_bench to a new file

merge web_bench and mini_bench because they serve similar purpose

make the --web default 
remove the CLI usage:
    python homebench.py --model qwen=http://localhost:8080 --model llama=http://localhost:8081
the python homebench.py --report can be an export button in the web

i recently refactored my application and now i get Run 1: FAIL
FAIL: expected string or bytes-like object, got 'NoneType'
[ERROR] expected string or bytes-like object, got 'NoneType'

Exception occurred during processing of request from ('127.0.0.1', 4528)
this error happens when i try to export the results

the auto-detected name of model is not working

1. append temperature as a note
2. fix the aliases as i think they are not used anymore
from tasks import TASKS
# Backward-compatible aliases for the extracted task check/explain functions.
from tasks import math as _t_math, logic as _t_logic, instructions as _t_instructions
from tasks import json_task as _t_json, code_task as _t_code, game as _t_game
from tasks import bulgarian as _t_bg
check_math, explain_math = _t_math.check, _t_math.explain
check_logic, explain_logic = _t_logic.check, _t_logic.explain
check_instructions, explain_instructions = _t_instructions.check, _t_instructions.explain
check_json, explain_json = _t_json.check, _t_json.explain
check_code, explain_code = _t_code.check, _t_code.explain
check_game, explain_game = _t_game.check, _t_game.explain
check_bg_article, explain_bg_article = _t_bg.check, _t_bg.explain
3. after i run the benchmark and is done the run benchmark button is grayed out
4. add tests for this

read @/History.md and verify the code and create tests
each statement in the history file should go with its own test file

127.0.0.1 - - [25/Oct/2026 20:47:45] "GET /.well-known/appspecific/com.chrome.devtools.json HTTP/1.1" 404 - is this normal for the server?

⚠️ **Security:** the *code* task executes model-generated Python locally. Only run models you trust.
hide this when the benchmark starts

i think there is a problem with parsing the output of the models, simple code generation shows as the code blocks not formatted correctly and this causes the results to fail

same problem for the game task as there is an html maybe the format is lost as well

update history.md as per agents.md

issue with format remains
this is the output of the game generation:
```
<!DOCTYPE html<html lang="en"<head    <meta charset="UTF-8"    <meta name="viewport" content="width=device-width, initial-scale=1.0"    <title    <style        body {
            display: flex;
            justify-content: center;
            align-items: center;
            min-height: 100vh;
            margin: 0;
```
and this is for code
```
import re

def is_palindrome(s: str) -    """
    Checks if a string is a palindrome, ignoring case and non-alphanumeric characters.
    """
    # 1. Convert to lowercase and keep only alphanumeric characters
    processed_s = re.sub(r'[^a-z0-9]', '', s.lower())

    # 2. Check if the processed string is equal to its reverse
    return processed_s == processed_s[::-1]
```

can you temporarly disable markdown to confirm its not interfering

FIXED: model output parsing strips ">" from code/HTML output, causing false failures.
Root cause: homebench.chat() used r"\]*?>.*?\n" and r"\]*?>.*$" to drop reasoning blocks,
but \]*?> matches a bare ">" and consumes the rest of the line. This corrupted every HTML
tag (<html lang="en"> -> <html lang="en">) and code comparison (-> -> -, a > b -> a b),
so code and game tasks failed even when the model output was fine.
Fix: replaced with _sanitize_output() which only removes <thinking>...</thinking> blocks
(and stray tags) and never touches ">" in normal output. Covered by
tests/test_history_29_output_sanitization.py.

RESTORED: markdown view for model output in the web UI (static/index.html).
The output was temporarily rendered as literal preformatted text to confirm
Markdown wasn't masking format. Now that the output parser no longer corrupts
">" in code/HTML, renderDetailRun uses outDiv.innerHTML = renderMarkdown(...)
again so code blocks format correctly. Raw HTML game output is still available
via extractHtml() -> iframe preview ("Render HTML inline" / "Open HTML in new tab").
1. make the next and prev buttons go trough all the tests, so if each test is 3/3 after you view the 3 pages, the next button should move to the next test, so from math it will go to logic
2. add option to edit the name of the model from the results page, and add colum showing the temperature

Review: Reject model renames while a benchmark is running, under the existing lock. See tests/test_history_30_rename_during_run.py.

Review: Write renamed JSONL results to a same-directory temporary file and replace atomically, preserving the original if writing fails. See tests/test_history_31_atomic_rename_write.py.

Review: Make the model rename control keyboard-accessible with Enter and Space while preserving click activation. See tests/test_history_32_keyboard_rename.py.

Review: Keep the mocked chat active for the full run_benchmark call in the temperature-column test. See tests/test_history_33_temperature_test_mock_scope.py.

update readme to be more descripitve and add how to guide

add as image screeenshot in the readme
