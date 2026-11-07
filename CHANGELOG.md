History Summary - HomeBench Benchmark Project (v1.2) - COMPLETE

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
- Real-time model output streaming: generated answer tokens and reasoning tokens stream from the model server to the web UI while a benchmark runs, keeping the page responsive and navigable during a run
- Live output panes scroll independently and do not force the page to scroll; auto-scroll only when the user is already at/near the bottom
- Latest stream remains visible after the run finishes
- Whole application is now wider

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
- HomeBench was silently converting a missing final answer from the model server into an empty string; diagnose and report empty final model content explicitly

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
- Invalid HOMEBENCH_CODE_TIMEOUT values now raise a configuration error

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
- Add date/time column showing each model's most recent benchmark time (local YYYY-MM-DD : HH:MM)
- Results sort newest first by default; clicking the date/time header reverses the order
- Total per run column renamed to "time"; elapsed time shown as minutes:seconds (e.g. 0:42, 2:12)
- Results table populates before the first test passes; incomplete tasks show "pending" instead of "-"
- Only the real running task shows "running"; pending rows keep no background
- Running marker scoped only to the current run (model + active task/run)
- Temperature column added

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
- Bulk delete: leading checkbox column, select-all (indeterminate-aware), single "Delete selected (N)" button
- Checkbox and delete-all-per-row combined in a single column
- Per-row (-) delete button removed
- Backend delete_models() rewrites results atomically; old filter API preserved

==================================================
SKIP / ABORT
==================================================
- Add button in the webui to skip the current task while it's running; make the table reflect if the test is run or skipped or pending
- Skip button re-enabled on each new run
- Exclude skipped runs from task and aggregate pass-rate denominators while keeping skip counts visible
- Interrupt active chat reads when skipping
- Create a fresh mocked response for each request (tests left pytest hanging because reusable mocked HTTP responses have no finite readline stream)
- Add abort test button next to skip that will cancel all of the run
- Abort passed through to both chat requests; should_abort can interrupt connection establishment instead of waiting for the full CHAT_TIMEOUT
- In-flight partially generated task is discarded on abort, not saved as a SKIPPED row; rows already on disk are kept

==================================================
GAME TASK (tasks/game.py)
==================================================
- Fix Python test suite to handle errors such as FAIL: could not check JS ('charmap' codec can't encode character '\U0001f33f' ...) — the problem is in the checker code, not the task
- Write the JS temp file with UTF-8 encoding so valid emoji JavaScript passes the checker
- Replace the hard-coded canvas dimension in the bounds validation with the applicable canvas width and height
- Resolve the complete radius expression rather than accepting only its leading number; reject unsupported or invalid expressions
- Update symbol resolution so reassigned variables reflect their latest value at spawn time
- Reject any divisor interval that contains zero, including zero strictly between its endpoints
- Use brace-aware helper-body extraction capturing the entire function body, including statements after nested blocks
- Recognize local coordinate variables, shorthand coin objects, trigonometric offsets, and collection handled by helper functions

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
- Live model output auto scroll
- Wider application layout
- Temperature plans saved to localStorage and restored on refresh

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
- Fix: JS temp file encoding causing charmap codec error on Windows
- Fix: skip support with should_skip callback
- Fix: running marker scoped to current run
- Fix: date/time format YYYY-MM-DD : HH:MM
- Fix: temperature plans persistence across refresh
- Fix: bulk delete with checkbox column
- Fix: time column m:ss format
- Fix: pending rows before first result
- Fix: abort run cancels whole run
- Fix: abort connection cancel via should_abort
- Fix: select-all checkbox synchronization
- Fix: game checker review regressions
- Fix: server constant polling rate

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