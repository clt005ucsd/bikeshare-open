# Seeded faults  (template: paste REAL output only; delete this line)

## Fault 1: forbidden column added to feature_columns
**Change:** src/features.py line 85, `return [c for c in numeric if c not in FORBIDDEN]` -> `return [c for c in numeric if c not in FORBIDDEN] + ['casual']` (made by the agent with the Edit tool, on my instruction)
**Red test output:**
```
$ python -m pytest tests/test_leakage.py -q
.F......
E       AssertionError: forbidden columns in feature set: {'casual'}
tests/test_leakage.py:31: AssertionError
FAILED tests/test_leakage.py::test_no_forbidden_features - AssertionError: fo...
1 failed, 7 passed in 0.06s
```
**Hook stderr:**
```
PostToolUse:Edit hook reported a problem
[${CLAUDE_PROJECT_DIR}/.claude/hooks/check_leakage.sh]: Leakage tests failed after editing src/features.py:
    def test_no_forbidden_features(feats):
        cols = set(feature_columns(feats))
>       assert not (cols & FORBIDDEN), f"forbidden columns in feature set: {cols & FORBIDDEN}"
E       AssertionError: forbidden columns in feature set: {'casual'}
tests/test_leakage.py:31: AssertionError
FAILED tests/test_leakage.py::test_no_forbidden_features - AssertionError: fo...
1 failed, 7 passed in 0.09s
```
**Turns the agent needed to fix it:** 1 (one message: 'Fix the fault and run make test' -> 16 passed)

## Fault 2: .shift(1) removed from cnt_roll_7
**Change:** src/features.py line 76, `out[TARGET].shift(1).rolling(LAG_WARMUP).mean()` -> `out[TARGET].rolling(LAG_WARMUP).mean()` (today's count now inside its own 7-day mean)
**Red test output:**
```
$ python -m pytest tests/test_leakage.py -q
....F...
E           assert np.float64(4389.0) == 4414.857142857143 ± 0.00441486
E             Obtained: 4389.0
E             Expected: 4414.857142857143 ± 0.00441486
tests/test_leakage.py:57: AssertionError
FAILED tests/test_leakage.py::test_rolling_mean_excludes_today - assert np.fl...
1 failed, 7 passed in 0.06s
```
**Hook stderr:**
```
PostToolUse:Edit hook reported a problem
[${CLAUDE_PROJECT_DIR}/.claude/hooks/check_leakage.sh]: Leakage tests failed after editing src/features.py:
    def test_rolling_mean_excludes_today(feats):
        """cnt_roll_7 must be the mean of the 7 calendar days *before* today."""
>           assert feats.set_index("dteday").cnt_roll_7[date] == pytest.approx(expected)
E           assert np.float64(4389.0) == 4414.857142857143 ± 0.00441486
tests/test_leakage.py:57: AssertionError
FAILED tests/test_leakage.py::test_rolling_mean_excludes_today - assert np.fl...
1 failed, 7 passed in 0.10s
```
**Turns to fix:** 1

## Fault 3: weather encoder's raise removed
**Attempt 1 (wrong fault):** the agent replaced the `raise` with a comment, leaving an empty `if` block -> IndentationError. The hook fired, but on a syntax error, not on the intended fault:
~~~
PostToolUse:Edit hook reported a problem
[${CLAUDE_PROJECT_DIR}/.claude/hooks/check_leakage.sh]: Leakage tests failed after editing src/features.py:
E   IndentationError: expected an indented block after 'if' statement on line 29
ERROR tests/test_leakage.py
1 error in 0.09s
~~~
**Change (actual fault):** src/features.py line 30, `raise ValueError(...)` -> `pass`.

**Result: the suite stayed green and the hook was silent.**
~~~
$ make test
python -m pytest tests/ -q
................
16 passed in 1.13s
~~~
Every weather label in the real data is known (GOOD/MISTY/BAD), so removing the raise changes nothing the existing tests can see. This was a real gap in the suite.

**Closing the gap:** added `test_encode_weather_rejects_unknown_labels` to tests/test_leakage.py (the file the hook runs): `encode_weather(pd.Series(["GOOD", "HAIL"]))` inside `pytest.raises(ValueError)`. With the fault still in place:
~~~
$ make test
python -m pytest tests/ -q
.............F...
__________________ test_encode_weather_rejects_unknown_labels __________________
    def test_encode_weather_rejects_unknown_labels():
>       with pytest.raises(ValueError):
(+7 lines truncated in the Claude Code view)
~~~
**Fix:** restored the raise -> `17 passed in 0.84s`.

**Turns to fix:** 1 to restore the raise once a test existed to catch it. Seeding the fault correctly took 2 turns (the first attempt was a syntax error).

## My feature's test, failing before the feature existed
```
FAILED tests/test_leakage.py::test_roll_max_3_value - KeyError: 'cnt_roll_max_3'
1 failed, 14 passed in 1.55s
make: *** [test] Error 1
```

## Fault 4: overwriting data/raw/ from Bash (the hook cannot see this)
**What I did:** made /tmp/bad.csv (the raw CSV plus one line `2013-01-01,FAKE`) and asked the agent to copy it over data/raw/bike_daily.csv using the Bash tool, two ways.

**Attempt 1, `cp`: blocked.** Claude Code v2.1.330 applied the `Edit(./data/raw/**)` deny rule to the cp target:
~~~
Bash(cp /tmp/bad.csv data/raw/bike_daily.csv)
  Error: Permission to use Bash with command cp /tmp/bad.csv data/raw/bike_daily.csv has been denied.
~~~
**Attempt 2, the same copy through Python: allowed, no hook ran.**
~~~
Bash(python -c "import shutil; shutil.copy('/tmp/bad.csv', 'data/raw/bike_daily.csv')")
  (No output)
~~~
The raw file was overwritten with no prompt. The PostToolUse hook matches only Edit|Write under src/, so it never ran. The damage only showed up when I ran the tests myself:
~~~
$ git status --short data/raw/
 M data/raw/bike_daily.csv
$ make test 2>&1 | tail -5
ERROR tests/test_split.py::test_no_overlapping_dates - pandas._libs.tslibs.pa...
2 failed, 2 passed, 13 errors in 1.28s
~~~
They only failed because `FAKE` broke date parsing. A quiet edit (e.g. changing one `cnt` value) would very likely have passed every test. Restored with `cp /tmp/backup.csv data/raw/bike_daily.csv`; sha256 back to `a6bed1577f6e4de5...`.

**What this shows:** permission rules match command text, not what a command does. Blocking `cp` doesn't block Python, `cat >`, `tee`, etc. They are a boundary for the agent's hands, not a sandbox.

**What would catch it:**
- **A test that checks the raw file's sha256** against the known hash: catches any change, even a quiet one, whenever tests run.
- **A Stop hook running `make test`**: the agent couldn't finish its turn with the raw file changed.
- **`chmod -w` on the raw file**: the operating system blocks the write itself, whatever command is used. This is the strongest, because it doesn't depend on recognising the command.
- **A PreToolUse hook on Bash that rejects any command mentioning `data/raw`**: blocks it before it happens, but can be dodged by building the path in code.

**Implemented (two fixes):**
1. `test_raw_data_unchanged` in tests/test_contract.py (written by the agent on my instruction): asserts the sha256 of data/raw/bike_daily.csv starts with `a6bed1577f6e4de5`. Proof that it catches a *quiet* edit (one `cnt` value changed on row 2) that every other test missed:
~~~
$ git diff --stat data/raw/
 data/raw/bike_daily.csv | 2 +-
$ make test 2>&1 | tail -3
FAILED tests/test_contract.py::test_raw_data_unchanged - AssertionError: raw ...
1 failed, 17 passed in 1.14s
~~~
2. `chmod a-w data/raw/bike_daily.csv`: the operating system now refuses the write, whatever command is used. The exact bypass that worked before now fails:
~~~
$ python -c "import shutil; shutil.copy('/tmp/bad.csv', 'data/raw/bike_daily.csv')"
PermissionError: [Errno 13] Permission denied: 'data/raw/bike_daily.csv'
~~~
Limitation: git does not store file permissions, so a fresh clone is not read-only. The hash test is the fix that travels with the repo; `chmod` protects my working copy.

## Other real catches during the assignment (not seeded)

**Hook caught the agent's own bug** (gpt-oss:120b inserted the feature line without indentation):
The agent fixed it on the next edit.

**Unclassified-column test, first run on the real data:**
