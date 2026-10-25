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