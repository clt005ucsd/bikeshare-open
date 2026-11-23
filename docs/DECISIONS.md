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
- 2026-11-23: Set CLAUDE_CODE_AUTO_COMPACT_WINDOW=60000 in settings.local.json because Claude Code did not recognise the model and assumed a 1M-token context.
- 2026-11-23: Noted that the starter's `Write(./data/raw/**)` deny rule never matches (Claude Code warns about it); only `Edit(./data/raw/**)` protects raw data.
- 2026-11-23: Feature: cnt_roll_max_3 = max of cnt over d-3..d-1. Availability: all three days are known before forecasting day d. Test checks its value on 2012-06-15 against a hand-computed max.
- 2026-11-23: Rejected the agent's first test (asserted the column was absent, so it could never fail) and replaced its pytest.skip with an assert by hand, so missing dates fail instead of passing silently.
- 2026-11-23: Switched from qwen3.5:9b (local) to gpt-oss:120b (Ollama cloud, paid) after the failing test: local steps took 20-25 minutes on 16 GB, and Ollama cloud had no Qwen model.
- 2026-11-23: Feature: cnt_roll_max_3 = max of cnt over d-3..d-1. Availability: all three days are known before forecasting day d. Test checks its value on 2012-06-15 against a hand-computed max.
- 2026-11-23: Rejected the agent's first test (asserted the column was absent, so it could never fail) and replaced its pytest.skip with an assert by hand, so missing dates fail instead of passing silently.
- 2026-11-23: Switched from qwen3.5:9b (local) to gpt-oss:120b (Ollama cloud, paid) after the failing test: local steps took 20-25 minutes on 16 GB, and Ollama cloud had no Qwen model.
- 2026-11-23: Kept cnt_roll_max_3: validation ridge R2 0.6475 -> 0.6851, MAE 832.9 -> 763.9; hgb R2 0.2185 -> 0.32. Above the 0.01 noise floor. Test set not consulted.
- 2026-11-23: Added test_raw_columns_contract. First run flagged holiday, mnth, season, weather, weekday, workday. Classified them in config.py as SOURCE_COLS (read by features.py) or UNUSED_COLS (season, redundant with month) rather than FORBIDDEN, since none of them leak. A new raw column now fails the test until someone classifies it.
- 2026-11-23: Seeded fault 3 (encode_weather raise -> pass) left all 16 tests green because the real data has no unknown labels. Added test_encode_weather_rejects_unknown_labels to test_leakage.py so the fault now fails a test and trips the hook.
