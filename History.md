one of the test keeps failing, is it possible to show the reasoning or output tokens of the model in real time instead of just the answer? the webui should be responsive and i should be able to scroll or view other pages or tasks

Request: Add real-time model reasoning/output token streaming to the web UI while keeping it responsive and navigable during a run.

in the Results table add date and time column and make it sort by default to be newest on top

Add date/time to Results and sort by newest benchmark first by default.

the weather test fails some times with a model output containing a web_fetch tool-call JSON for wttr.in; it seems like the model attempted to retrieve the real result but did not provide a final temperature answer.

Clarify that HomeBench does not execute tool calls; reject and explain emitted web_fetch/curl requests when the model provides no final Celsius answer.

Supersede that behavior: execute the weather task's exact allowlisted wttr.in web_fetch request, return only the observed Celsius temperature to the model for its final answer, and never execute arbitrary URLs or shell tools.

but i want to actually be able to execute tool calls, makes sense right?
