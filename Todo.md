Timeouts are set in two task files:

tasks/code_task.py:26 — subprocess.run(..., timeout=10) (code execution)
tasks/game.py:92 — subprocess.run(..., timeout=30) (browser runtime check) and --virtual-time-budget=6000 (line 90); tasks/game.py:152 — node --check timeout=10
Yes, each can be increased by editing those values. The [ERROR] timed out message comes from the browser runtime check (timeout=30); the FAIL: execution timed out from code execution (timeout=10).

132 t/s


how long is this 10 or 30
The user is asking "how long is this 10 or 30". They want to know the units. The subprocess.run timeout is in seconds. So 10 = 10 seconds, 30 = 30 seconds.

Seconds. 10 = 10 seconds (code execution / JS syntax check), 30 = 30 seconds (browser runtime check). The --virtual-time-budget=6000 is milliseconds (6 seconds of virtual browser time).

170.6 t/s
is this timeout process blocking? is the app continueing?
The user asks whether the timeout process is blocking and whether the app continues. subprocess.run is blocking (synchronous), so when it times out, subprocess.TimeoutExpired is raised and caught, returning a failure result. The app continues with the next task/check. So yes, it blocks only that particular check, then continues.

Yes, each subprocess.run is blocking (synchronous) — it waits up to the timeout, then raises subprocess.TimeoutExpired, which is caught and returns a failure result ("FAIL: ... timed out"). The app then continues to the next task/check; it does not crash or hang.