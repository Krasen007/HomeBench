1. i want to create a new benchmark to test llm models
2. tell me what tools i need to create it?
3. can it be super simple with just 5 tasks for example, its just a demo to test few simple models.
i will use llama.cpp with small local models
in @/mini_bench.py implement F:\AI\repos\HomeBench\GameDesignDocument.md as a test in the suite of tasks
make the web interface render correctly markdown
for each pass or fail show the passing or failing condition in the answer
when i run the same model multiple times Model name (label for the table) should not replace the last results, add automatic increments, also it should be possible to infer the name of the model from llama.cpp
one of the current tasks is to create a single html application, i want to be able to view the resulting html from the results of the task, maybe add a button to show in external page or render it inside the current page