read @/History.md and make a new @/CHANGELOG.md file for bump 1.2

1. in the webview when a benchmark is started it shows the current task as running, can we make it show when is reasoning and when is generating answer, maybe change the text in the table. 2. some weak models start to loop and when i see it in the generated answer i would go and manually skip the current task, is it possible to detect if the model loops and we auto skip it?

Mapped to tests/test_history_83_running_phase_and_loop_autoskip.py.

1. if looping is detected it should be marked as failed, then continue to the next test in the suite. 2. point the tests at History-v1.2.md

Mapped to tests/test_history_84_loop_failure_and_archived_history.py. The loop auto-skip behavior in test_history_83 no longer applies; test_history_83 now covers only the reasoning/generating phase text.

only fix Fix the pass condition: in _weather_status, when expected_temperature is supplied, accept a bare number that equals the observation (keep the unit requirement for the standalone check() path); optionally also change the follow-up wording to show 13.0°C.

Mapped to tests/test_history_85_weather_bare_observation_answer.py.

when i run the benchmark i want to be able to read the reasoning tokens and the generated answer for each task, currently its showing it only when the model writes it but after that i cannot audit it, we should think of a way to optimize the web ui to incorporate everything that will serve a purpose the Live model output and the detail card

Mapped to tests/test_history_86_reasoning_audit_in_results.py.

Review comment at @homebench.py around lines 364 - 376:
Update both chat invocation paths in run_benchmark to always pass capture_token as the token callback, regardless of whether on_token is set. Keep capture_token’s existing guard when forwarding tokens to on_token so reasoning is recorded without requiring an external callback.

Mapped to tests/test_history_87_reasoning_capture_without_live_callback.py.

we tried to add some sort of loop detection, but now i got this, can you check? Now, let's write the code.

We'll also need to handle the spawn interval reduction: we'll set spawnInterval to a random between 0.3 and 0.8 seconds when the condition is met. We'll need to ensure that the spawn interval is in milliseconds.

Now, let's write the code.

We'll also need to handle the spawn interval reduction: we'll check after each yellow coin collection if the time since last collection is less than current spawnInterval. We'll need to know when the last collection occurred. We'll store lastCollectionTime. We'll update it on each collection.

Now, let's write the code.

We'll also need to handle the spawn interval reduction: we'll set spawnInterval to a random between 0.3 and 0.8 seconds when the condition is met. We'll need to ensure that the spawn interval is in milliseconds.

Now, let's write the code.

We'll also need to handle the spawn interval reduction: we'll check after each yellow coin collection if the time since last collection is

Mapped to tests/test_history_88_long_cycle_loop_detection.py.

it should fail and trigger as soon as the same appears 4 times

Mapped to tests/test_history_89_loop_trigger_after_four_repeats.py.

Keep the punctuation guard (line.endswith(...)) to protect code structures.

Run a quick sweep on the test suite after cleaning up any dead on_token mock signatures to see if those 3 pre-existing failures clear up.

Mapped to tests/test_history_04_pass_fail_conditions.py, tests/test_history_10_live_results.py, tests/test_history_53_empty_model_answer_diagnostics.py, tests/test_history_54_checkbox_task_selection.py.