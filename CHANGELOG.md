
History Summary - HomeBench Benchmark Project (v1.1) - COMPLETE

All sections verified and saved successfully.

==================================================
INITIAL TASKS & REQUIREMENTS
==================================================
- Determine tools needed to create a benchmark
- Can be super simple with just 5 tasks for demo purposes
- Implement GameDesignDocument.md as test in mini_bench.py
- Use llama.cpp with small local models

==================================================
WEB INTERFACE & MARKDOWN RENDERING
==================================================
- Make web interface render markdown correctly
- Show passing/failing condition for each pass/fail
- Model name should not replace last results when running same model multiple times
- Add automatic increments for model names
- Infer model name from llama.cpp output
- Render HTML inline above the answer (below the button)
- Add button to open HTML in new tab
- Move next/prev buttons to top
- Move render inline and open HTML buttons above the code

==================================================
EXTRACTION & ORGANIZATION
==================================================
- Extract all tasks and checks into separate files into a new folder
- Extract HTML from web_bench to a new file
- Merge web_bench and mini_bench because they serve similar purpose
- Extract CSS from static/index.html into static/style.css

==================================================
BUG FIXES & ISSUES
==================================================
- Viewing results in web view: results show then hide during benchmark run
- Fix output parsing that strips ">" from code/HTML output causing false failures
- Root cause: homebench.chat() regex patterns consuming content after ">"
- Fix: replaced with _sanitize_output() which only removes <thinking>...</thinking> blocks
- Model output parsing strips ">" causing code blocks to not format correctly
- Game task HTML format loss issue
- Fix verified: model output parsing no longer strips ">" from normal output

==================================================
SECURITY & WARNINGS
==================================================
- Add security warning for code_task: model-generated code executed locally
- Warning should appear in both CLI and web UI
- Consider sandboxing options

==================================================
EMPTY STATE IMPROVEMENT
==================================================
- Replace "No results yet. Run a model above." with welcoming message
- Show 7 task IDs with brief descriptions so new user knows what will be tested

==================================================
CLI & CONFIGURATION
==================================================
- Make --web default
- Remove CLI usage: python homebench.py --model qwen=http://localhost:8080 --model llama=http://localhost:8081
- python homebench.py --report can be export button in web
- Add task_id parameter to run only single task from task list
- /api/run accepts "task" field validated against known task IDs
- Web UI shows "Task" dropdown (default "All tasks")
- Progress total adjusts to runs * 1 when single task selected
- Replace single-task dropdown with checked task-selection boxes
- Allow running any non-empty subset
- Preserve legacy API task field
- Set progress totals from selected tasks

==================================================
RESULTS TABLE ENHANCEMENTS
==================================================
- Make columns sortable (model, temperature, any task, total, total per run)
- Sort by overall pass rate, not as task ID
- Add up/down indicator next to sorted column label
- Repeat column labels in footer row at bottom of results table
- Make columns resizable
- Show elapsed time for each run and/or average as column
- Update avg time column to show total per run not average per all tasks

==================================================
DELETE FUNCTIONALITY
==================================================
- Add option to delete individual runs or model+task groups
- homebench.delete_rows() removes rows matching filter criteria
- /api/delete_rows POST endpoint validates filters and delegates to delete_rows
- Web UI shows × delete button on each results-table cell (deletes all runs for that model+task)
- "Delete this run" button in detail view (deletes single run)
- Both prompt for confirmation before deleting
- Delete rows functionality should show only 1 (-) sign for whole row, not next to each test

==================================================
WEATHER TASK
==================================================
- Add agentic weather task testing model tool/skill usage
- Embed openclaw weather skill in prompt
- Ask model to check weather in Varna for today, answer with temperature in Celsius
- Model should read skill, formulate wttr.in API call, extract current_condition[0].temp_C
- Accept bare "celsius" suffixes
- Accept bare "C" temperature suffix such as "14 C"
- Use deterministic weather fixture instead of formatting-only validation
- Prompt supplies simulated Varna observation
- Checker requires bare Celsius answer matching exact temperature
- Load complete pinned OpenClaw SKILL.md from user-provided local tasks/weather_SKILL.md
- If absent, report task as unavailable
- Weather benchmark should not give away expected JSON field
- Should not tell model to ignore injected instructions

==================================================
TESTING
==================================================
- Add tests for various features
- Each statement in history file should go with its own test file
- Fix failing tests related to aliases (remove aliases, update tests)
- test_history_29_output_sanitization.py
- test_history_30_rename_during_run.py
- test_history_31_atomic_rename_write.py
- test_history_32_keyboard_rename.py
- test_history_33_temperature_test_mock_scope.py
- test_history_36_weather_formatting_scope.py
- test_history_37_weather_fixture_extraction.py
- test_history_38_weather_skill_injection.py

==================================================
UI/UX IMPROVEMENTS
==================================================
- Move next/prev buttons to top
- Real-time results viewing during benchmark run
- Multi-selection tool for temperature values and run counts (e.g., 1× at 0.0, 3× at 0.6, 3× at 1.0)
- Add checkboxes to select which tasks to run
- Replace single-task dropdown with checked task-selection boxes
- Add "Delete this run" button in detail view
- Add "Delete this run" confirmation prompt
- Sortable columns with footer labels
- Resizable columns

==================================================
TECHNICAL FIXES
==================================================
- Fix: model output parsing strips ">" from code/HTML output
- Fix: aliases redundancy - remove them, update tests
- Fix: auto-detected model name not working
- Fix: view results in real time during benchmark run
- Fix: render HTML inline actually show render above answer
- Fix: add temperature column
- Fix: start.bat should verify needed requirements
- Fix: older benchmarks not appearing, new ones not displaying
- Fix: results-table fields not sortable
- Fix: game task not displaying results (filter issue)
- Fix: game_solved empty output issue
- Fix: diagnose and report empty final model content explicitly
- Fix: code blocks not formatted correctly causing result failures

==================================================
README & DOCUMENTATION
==================================================
- Update readme to be more descriptive and add how-to guide
- Add as image screenshot in the readme

==================================================
ONGOING DEVELOPMENT
==================================================
- Continue adding tasks and improving checks
- Real-time results display during benchmark execution
- Enhanced model name handling with increments
- Improved web interface and user experience