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
**Change:** [..]
**Red test output:**
```
[paste]
```
**Hook stderr:**
```
[paste]
```
**Turns to fix:** [n]

## My feature's test, failing before the feature existed
```
FAILED tests/test_leakage.py::test_roll_max_3_value - KeyError: 'cnt_roll_max_3'
1 failed, 14 passed in 1.55s
make: *** [test] Error 1
```

## Fault 4: cp into data/raw/ from Bash (the hook cannot see this)
**What I did:** [..]
**What happened:** [no hook fired because PostToolUse matches Edit|Write, not Bash; ..]
**What would catch it:** [PreToolUse hook on Bash / chmod -w data/raw / sha256 check in make data, and why]
**Implemented?** [no / yes + diff]


## Other real catches during the assignment (not seeded)

**Hook caught the agent's own bug** (gpt-oss:120b inserted the feature line without indentation):
The agent fixed it on the next edit.

**Unclassified-column test, first run on the real data:**
