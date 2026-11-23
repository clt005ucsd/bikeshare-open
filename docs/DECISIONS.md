# Decisions

One line per methodological decision: what you chose, why, and what it changed.
Agents append here via the `/new-feature` skill; you append here by hand.

- Exclude `casual`, `registered`: they sum to `cnt` exactly. Leaky model R^2 1.000 -> honest ridge 0.583.
- Exclude `cnt_2d_bfr`: a shipped 2-day lag we cannot test the alignment of. Build our own lags instead.
- Exclude `instant`, `yr`, `days_since_2011`: time indexes let a tree predict a flat constant past 2011 and a linear model extrapolate a trend we have no grounds for.
- Split 2011 / H1 2012 / H2 2012 by date. Test set touched once, after all feature work.
- Report mean and persistence baselines with every score. Persistence (test R^2 0.510, MAE 840) is within 0.07 R^2 of ridge and beats it on MAE; that caveat goes in the report.
- 2026-11-23: Used Python 3.12 via uv instead of Anaconda's 3.11, because the pinned numpy==2.5.3 needs Python >=3.12 (and Anaconda's conda solver is broken on this machine).
- 2026-11-23: Built bikeshare-coder (qwen3.5:9b, num_ctx 65536) from a temporary Modelfile because `ollama create -f -` failed on Ollama 0.40.17; Makefile left unchanged.
- 2026-11-23: Set CLAUDE_CODE_AUTO_COMPACT_WINDOW=60000 in settings.local.json because Claude Code did not recognise the model and assumed a 1M-token context. In practice Claude Code clamps this setting to a 100k minimum, so compaction kicks in around 100k tokens, not 60k.
- 2026-11-23: Noted that the starter's `Write(./data/raw/**)` deny rule never matches (Claude Code warns about it); only `Edit(./data/raw/**)` protects raw data.
- 2026-11-23: Feature: cnt_roll_max_3 = max of cnt over d-3..d-1. Availability: all three days are known before forecasting day d. Test checks its value on 2012-06-15 against a hand-computed max.
- 2026-11-23: Rejected the agent's first test (asserted the column was absent, so it could never fail) and replaced its pytest.skip with an assert by hand, so missing dates fail instead of passing silently.
- 2026-11-23: Switched from qwen3.5:9b (local) to gpt-oss:120b (Ollama cloud, paid) after the failing test: local steps took 20-25 minutes on 16 GB, and Ollama cloud had no Qwen model.
- 2026-11-23: Kept cnt_roll_max_3: validation ridge R2 0.6475 -> 0.6851, MAE 832.9 -> 763.9; hgb R2 0.2185 -> 0.32. Above the 0.01 noise floor. Test set not consulted.
- 2026-11-23: Added test_raw_columns_contract. First run flagged holiday, mnth, season, weather, weekday, workday. Classified them in config.py as SOURCE_COLS (read by features.py) or UNUSED_COLS (season, redundant with month) rather than FORBIDDEN, since none of them leak. A new raw column now fails the test until someone classifies it.
- 2026-11-23: Seeded fault 3 (encode_weather raise -> pass) left all 16 tests green because the real data has no unknown labels. Added test_encode_weather_rejects_unknown_labels to test_leakage.py so the fault now fails a test and trips the hook.
- 2026-11-23: Fault 4: the Edit deny rule blocked a Bash cp into data/raw but not python shutil.copy, and no hook ran. Added test_raw_data_unchanged (sha256 prefix a6bed1577f6e4de5), which caught a quiet one-value edit that all 17 other tests missed; also chmod a-w on the raw CSV locally (not carried by git).
- 2026-11-23: Ex 4: added TARGET_DIFF=1 to src/train.py. hgb is fit on cnt - cnt_lag_1 and cnt_lag_1 is added back before scoring; results go to reports/metrics_diff.json so metrics.json stays the untransformed run. Validation: hgb R2 0.32 -> 0.6198, MAE 1198.0 -> 816.9. That now beats persistence (0.4507 / 900.6) but is still behind ridge (0.6851 / 763.9). Trees can't extrapolate above the 2011 range; predicting the day-to-day change removes that ceiling. Note: the agent's first flagged run printed the full JSON, test numbers included, but it was collapsed in the UI and I didn't expand it.
- 2026-11-23: Test set read once, at the end, for REPORT.md: ridge test R2 0.6001 vs persistence 0.5099, but MAE 906.8 vs 840.1. My feature did not change the starter's caveat that persistence beats ridge on MAE. TARGET_DIFF hgb test 0.5632 / 896.5. No changes made after reading test.
