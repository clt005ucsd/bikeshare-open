# Audit

Worked solo, so there was no peer to audit my branch. Instead I audited it in a fresh Claude Code session (`/clear`) that had never seen the session that wrote the code, using the repo's `leakage-auditor` subagent.

## Audit 1: branch feature/roll3-max (commit 44a085c) vs main
**How I kept it independent:** ran `/clear` first; the auditor subagent was given only the branch name and `git diff main...feature/roll3-max`, not my conversation history.

**leakage-auditor output (verbatim, as returned to the main session after 38s):**
~~~
All five checks pass. No findings.
~~~

**My verdict:** I agree with the conclusion, but the auditor showed no evidence: no file:line references and no commands run that were visible to me. A bare "pass" isn't something I'd trust, so I checked each point myself:

1. **Target leakage / temporal ordering.** The only feature change is `src/features.py:77`, `out["cnt_roll_max_3"] = out[TARGET].shift(1).rolling(3).max()`. The shift happens before the rolling window. To check it numerically, I set the 2012-06-15 `cnt` to 99999 and rebuilt the features:
~~~
rows raw/feat: 728 714
06-15 feature, before/after spiking 06-15 cnt: 7421.0 7421.0
06-16 feature after spike: 99999.0
~~~
Today's count doesn't change today's feature; it first shows up the next day. So there's no same-day leakage, and the lag is exactly 1 day.
2. **Calendar gaps / silent row loss.** `n_train` (348) and `n_valid` (182) are the same on main and on the branch (`git diff main...feature/roll3-max -- reports/metrics.json` only changes `n_features` 14 -> 15). The 3-day window needs less history than the existing `cnt_roll_7`, so it adds no new NaN rows for `dropna()` to drop.
3. **Unreported baselines.** `reports/metrics.json` still has `baseline_mean` and `baseline_persistence` for valid and test.
4. **Tests fail on leakage.** Shown in docs/SEEDED_FAULTS.md: removing the shift (fault 2) and adding `casual` (fault 1) both turned the suite red.

**One thing the auditor missed** (it's on main, not in this diff): the starter's `test_rolling_mean_excludes_today` sits behind an `if all(...)` guard, so it can pass without asserting anything. That's why I added an exact-value test for my own feature (`test_roll_max_3_value`) instead of relying on the same pattern.

## Batch auditor on my final repo
`python agent/audit.py . --out reports/audit.jsonl`
Run with gpt-oss:120b on Ollama cloud (`AUDIT_MODEL=gpt-oss:120b`). Output (the `[claude-code:unrecognized_model]` warning is just Claude Code not knowing the model name):
~~~
audited 1 repos; 1 flagged -> reports/audit.jsonl
{"repo": "bikeshare-open", "baseline_reported": true, "confidence": "high", "findings": [{"file": "data/processed/features.csv", "issue": "target leakage: 'casual' + 'registered' == 'cnt'", "line": 1, "why_it_matters": "Provides perfect prediction, violating the project's rule against leakage and inflates model performance."}], "leakage": "confirmed", "reproducible": true, "temporal_ok": true}
~~~

**My verdict: false positive, with high confidence attached to it.** The identity itself is real: `casual` and `registered` are columns in the processed table, and they do sum to `cnt`. But a column being in the table doesn't mean the model uses it. `feature_columns()` (`src/features.py:82-85`) removes everything in `FORBIDDEN`, and `casual` and `registered` are in `LEAKAGE_COLS`. The model's actual inputs are listed in `reports/metrics.json` under `"features"`: 15 columns, neither of those two. Fault 1 in SEEDED_FAULTS.md shows what happens if `casual` does get into the feature list: the leakage test fails. So leakage of the model inputs is "none", not "confirmed".

**Something more interesting it showed:** `data/processed/features.csv` isn't produced by the pipeline (which writes `features.parquet`), and its timestamp is the same minute as the audit run. The auditor wrote that file itself, through Bash. The comment in `agent/audit.py` says the auditor "has no Edit or Write to grant", but with `Bash` allowed it can still write files. It's the same lesson as fault 4: tool permissions restrict which tool gets used, not what the commands do. The file is git-ignored, so it didn't end up in the repo, and I deleted it.
