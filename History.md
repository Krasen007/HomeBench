read @/History.md and make a new @/CHANGELOG.md file for bump 1.2

1. in the webview when a benchmark is started it shows the current task as running, can we make it show when is reasoning and when is generating answer, maybe change the text in the table. 2. some weak models start to loop and when i see it in the generated answer i would go and manually skip the current task, is it possible to detect if the model loops and we auto skip it?

Mapped to tests/test_history_83_running_phase_and_loop_autoskip.py.