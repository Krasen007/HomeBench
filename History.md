read @/History.md and make a new @/CHANGELOG.md file for bump 1.2

1. in the webview when a benchmark is started it shows the current task as running, can we make it show when is reasoning and when is generating answer, maybe change the text in the table. 2. some weak models start to loop and when i see it in the generated answer i would go and manually skip the current task, is it possible to detect if the model loops and we auto skip it?

Mapped to tests/test_history_83_running_phase_and_loop_autoskip.py.

1. if looping is detected it should be marked as failed, then continue to the next test in the suite. 2. point the tests at History-v1.2.md

Mapped to tests/test_history_84_loop_failure_and_archived_history.py. The loop auto-skip behavior in test_history_83 no longer applies; test_history_83 now covers only the reasoning/generating phase text.

only fix Fix the pass condition: in _weather_status, when expected_temperature is supplied, accept a bare number that equals the observation (keep the unit requirement for the standalone check() path); optionally also change the follow-up wording to show 13.0°C.

Mapped to tests/test_history_85_weather_bare_observation_answer.py.