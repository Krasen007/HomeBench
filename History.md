one of the test keeps failing, is it possible to show the reasoning or output tokens of the model in real time instead of just the answer? the webui should be responsive and i should be able to scroll or view other pages or tasks

Request: Add real-time model reasoning/output token streaming to the web UI while keeping it responsive and navigable during a run.

in the Results table add date and time column and make it sort by default to be newest on top

Add date/time to Results and sort by newest benchmark first by default.

the weather test fails some times with a model output containing a web_fetch tool-call JSON for wttr.in; it seems like the model attempted to retrieve the real result but did not provide a final temperature answer.

Clarify that HomeBench does not execute tool calls; reject and explain emitted web_fetch/curl requests when the model provides no final Celsius answer.

Supersede that behavior: execute the weather task's exact allowlisted wttr.in web_fetch request, return only the observed Celsius temperature to the model for its final answer, and never execute arbitrary URLs or shell tools.

but i want to actually be able to execute tool calls, makes sense right?

for the game.py task i am wondering can the python test suite be fixed to handle errors such as FAIL: could not check JS ('charmap' codec can't encode character '\U0001f33f' in position 4459: character maps to <undefined>)
i think the problem is not in the task because the game works but the checker code

make the Live model output Generated answer auto scroll

make the width of the whole application more wide

add button in the webui to skip the current task while its running, make the table reflect if the test is run or skipped or pending

Fix review findings: interrupt active chat reads when skipping; re-enable the Skip task button on each new run; exclude skipped runs from task and aggregate pass-rate denominators while keeping skip counts visible; assert valid emoji JavaScript passes the checker; and create a fresh mocked response for each request.

tests\test_homebench.py passes but leaves pytest hanging because reusable mocked HTTP responses have no finite readline stream; create fresh, EOF-terminating responses for each request.

lets run the whole suite and check if everything is ok