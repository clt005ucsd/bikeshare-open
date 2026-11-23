# REPORT

Clayton Tan, solo. Repo: bikeshare-open. The feature work is on branch `feature/roll3-max`, merged into `main`.

## Results
Validation and test R² / MAE, copied exactly from reports/metrics.json ("before" = unmodified starter, commit eb15d74; "after" = with my feature `cnt_roll_max_3`).

| Model | Feature set | Valid R² | Valid MAE | Test R² | Test MAE |
|---|---|---|---|---|---|
| baseline_mean | before | -0.9318 | 2002.2 | -2.1441 | 2847.7 |
| baseline_persistence | before | 0.4507 | 900.6 | 0.5099 | 840.1 |
| ridge | before | 0.6475 | 832.9 | 0.5833 | 947.1 |
| hgb | before | 0.2185 | 1296.6 | -0.4975 | 1972.6 |
| baseline_mean | after | -0.9318 | 2002.2 | -2.1441 | 2847.7 |
| baseline_persistence | after | 0.4507 | 900.6 | 0.5099 | 840.1 |
| ridge | after | 0.6851 | 763.9 | 0.6001 | 906.8 |
| hgb | after | 0.32 | 1198.0 | -0.4228 | 1913.6 |

(The baselines don't change between before and after. The mean baseline uses no features, and persistence only uses `cnt_lag_1`, so neither touches the new column.)

## Headline finding
**On the held-out H2 2012 test set, the best model (ridge) still makes bigger day-to-day errors than just predicting yesterday's count.** Ridge explains more variance than persistence (test R² 0.6001 vs 0.5099), but its typical miss is larger (MAE 906.8 vs 840.1 rides/day). The gradient-boosted model does worse than both (test R² -0.4228): trees trained on 2011 can't predict above 2011's range, and 2012 ridership is about 65% higher. The mean baseline (R² -2.14) shows how far the level moved between years. My feature, `cnt_roll_max_3` (max of the previous 3 days' counts, shifted by one day), improved **validation** ridge from R² 0.6475 / MAE 832.9 to 0.6851 / 763.9 and hgb from 0.2185 to 0.32, so I kept it. That decision was made before I looked at any test numbers.

## Exercise 4: target transformation
**Transformation:** behind the flag `TARGET_DIFF=1` (src/train.py), hgb is fit on `cnt - cnt_lag_1` (the change from yesterday) and `cnt_lag_1` is added back before scoring. Every other model is unchanged. Flagged runs write to `reports/metrics_diff.json`, so `metrics.json` stays the untransformed run (checked: with the flag off, `git diff reports/metrics.json` is empty).

| hgb | Valid R² | Valid MAE | Test R² | Test MAE |
|---|---|---|---|---|
| raw target | 0.32 | 1198.0 | -0.4228 | 1913.6 |
| TARGET_DIFF | 0.6198 | 816.9 | 0.5632 | 896.5 |

**Test run once:** the test numbers come from the single flagged run, and I read them once at the end, when writing this report. I changed nothing after that.

**Defensible, or does it just win the comparison?** I think it's defensible. I chose it for a reason I had *before* seeing any results: CLAUDE.md already says trees can't extrapolate the 2011→2012 growth. Predicting the daily change removes that ceiling, because a day-to-day change in 2012 looks like a day-to-day change in 2011 even though the level doesn't. It's a single choice, not something I picked from several tries. The honest caveat is that it's basically "persistence plus a learned correction". It beats persistence on R² (0.5632 vs 0.5099) but still loses on MAE (896.5 vs 840.1), and on validation it's still behind ridge. So it rescues hgb from being broken, but it doesn't make hgb the model to use.

## Exercise 5: ridge vs persistence
Ridge isn't clearly worth deploying over "yesterday again", and which one wins depends on the metric. On test, ridge has higher R² (0.6001 vs 0.5099) but worse MAE (906.8 vs 840.1). That means ridge is better on the big swing days, the weather-driven drops and spikes where persistence is badly wrong (R² punishes large errors most). On a typical day, though, it's about 67 rides further off. Validation had ridge winning on both metrics (MAE 763.9 vs 900.6), so this flips on H2 2012. My guess is that the seasonal decline in autumn and winter, plus outliers like Hurricane Sandy (2012-10-29, 22 rides), matter here, but I haven't tested that. Persistence also needs no training, no feature pipeline and nothing that can break. I'd only deploy ridge if the cost of a forecast miss is mostly about the large misses (like running out of bikes on a surprise busy day). If ordinary daily accuracy is what counts, persistence is the honest choice, and ridge hasn't earned its extra complexity yet.

## Attribution
Model: qwen3.5:9b via Ollama (local `bikeshare-coder` build, num_ctx 65536) for setup and writing the failing test. I switched to **gpt-oss:120b via Ollama cloud** (paid) after that step, because local steps took 20–25 minutes each on a 16 GB laptop and Ollama cloud had no Qwen model (DECISIONS, 2026-11-23).
Also used: **Claude (claude.ai chat, outside the harness).** It wrote the setup script, the prompts I gave the agent, and the templates for this report and the docs. It also turned my terminal output into the write-ups in docs/SEEDED_FAULTS.md, docs/AUDIT.md, DECISIONS lines and this report, and suggested the verification commands (the 99999 spike check, the sha256 check). All the numbers and outputs quoted come from commands I ran myself in my terminal or in Claude Code.

Agent-generated (files / functions), all through the Claude Code harness:
- `src/features.py:77`: `cnt_roll_max_3`
- `tests/test_leakage.py`: `test_roll_max_3_value` (I replaced its `pytest.skip` with an assert by hand) and `test_encode_weather_rejects_unknown_labels`
- `tests/conftest.py`: the `raw` fixture
- `tests/test_contract.py`: `test_raw_columns_contract` and `test_raw_data_unchanged`
- `src/config.py`: `SOURCE_COLS`, `UNUSED_COLS`
- `src/train.py`: the `TARGET_DIFF` flag
- `.claude/skills/seed-fault/SKILL.md` (step 2 fixed afterwards, with Claude's help, so untracked files don't count as a dirty tree)
- the seeded faults themselves and their reverts; docs/AUDIT.md's first draft (a one-line "no findings", replaced by the evidence-based version)

My decisions (each traces to a line in docs/DECISIONS.md):
- **What to predict:** daily `cnt`, plus (Ex 4) the alternative of predicting `cnt - cnt_lag_1` for hgb only, behind a flag.
- **What counts as leakage:** anything built from the same day's `cnt` or its parts. That's why I kept `.shift(1)` before `.rolling(3)`, and why the new raw columns went into SOURCE/UNUSED and not FORBIDDEN (none of them leak). I argued the batch auditor's `casual + registered` flag as a false positive (AUDIT.md).
- **How to split:** I kept the starter's 2011 / H1 2012 / H2 2012 date split. The test set was read once, at the end.
- **Which baselines:** mean and persistence reported with every model, including in the Ex 4 table.
- **Whether to keep my feature:** kept, based on validation only (ridge R² +0.038, MAE −69).
- **Whether the answer is believable:** partly. Ridge's lead over persistence is real on R² but reverses on MAE out of sample, so I don't claim ridge is the better forecaster.
