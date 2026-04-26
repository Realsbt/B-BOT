# 80+ Statistical Rigour Upgrade Plan

## Purpose

This plan is for strengthening the final report from a strong first-class engineering validation into a more credible 80+ candidate. It does not guarantee an 80+ mark. The aim is to reduce the main marking risk identified in review: the physical control experiments are currently small-sample, manually disturbed, and closer to engineering validation than controlled statistical experimentation.

The most valuable upgrade is not to add more broad features. It is to make E2 and E9 more repeatable, more transparent, and better analysed at trial level.

## Current Weak Point

The report already has strong evidence for:

- embedded implementation depth;
- local ESP32 balance-loop timing;
- WiFi and vision as supervisory command paths;
- O3 safety arbitration;
- public software evidence;
- measured E1-E11 datasets.

The remaining 80+ risk is:

- E2 and E9 use small physical trial counts;
- disturbance inputs are manually applied;
- most physical control results are reported as mean values or pass/fail counts;
- uncertainty is acknowledged but not yet quantified in detail.

This is acceptable for 70+, but for a safer 80+ profile the report should show trial-level spread, confidence intervals, and an explicit small-sample interpretation.

## Upgrade Scope

Prioritise only the experiments that affect the main control contribution:

| Priority | Experiment | Current role | Upgrade target |
|---|---|---|---|
| 1 | E9 controller ablation | Main comparative baseline for LQR/VMC design choices | Add more FULL and FIXED_LQR trials, report uncertainty and effect size |
| 2 | E2 disturbance recovery | Main recovery evidence for O1 | Add more forward/backward trials, report uncertainty and failure handling |
| 3 | Appendix G statistics | Evidence traceability | Add trial-level statistical summaries without increasing main-body length much |

Do not spend time expanding E5, E8, E10 or E11 unless a specific inconsistency is found. E5/E8/E11 already have larger sample counts or clear latency/jitter distributions. The physical control tests are the bottleneck.

## Additional Data Collection

### E9 Controller Ablation

Recommended minimum:

| Condition | Add trials | Final target |
|---|---:|---:|
| FULL impulse recovery | +10 | 20 trials |
| FIXED_LQR impulse recovery | +10 | 20 trials |
| NO_RAMP drive step | Optional +10 | 10-20 trials |

FULL and FIXED_LQR are the key pair because they directly test whether leg-length gain scheduling improves recovery. NO_RAMP is useful, but it is a different drive-step protocol, so it should remain a narrower command-conditioning result.

For each trial, record:

- controller mode;
- trial index;
- success/failure;
- protection trigger;
- response metric;
- peak pitch;
- settling time if applicable;
- battery state if available;
- leg length / controller parameter version;
- short note if the trial had an obvious operator error.

All failed or protected trials must be retained. Do not remove failed trials to improve the result.

### E2 Disturbance Recovery

Recommended minimum:

| Direction | Add trials | Final target |
|---|---:|---:|
| Forward disturbance | +10 | 20 trials |
| Backward disturbance | +10 | 20 trials |

Forward is more important because the current result already shows the weaker case: 9/10 successful recoveries and one protection event.

For each trial, record:

- direction;
- trial index;
- success/failure;
- protection trigger;
- peak pitch deviation;
- settling time;
- maximum wheel speed;
- final recovery status;
- note if the manual push was visibly abnormal.

Again, abnormal trials should normally be retained and annotated, not deleted.

## Test Control Conditions

To make manually applied tests more defensible, keep these conditions fixed:

- same operator for all new E2/E9 disturbance trials;
- same floor surface;
- same robot configuration and firmware commit;
- same controller gains;
- similar battery state, or record battery voltage if available;
- same startup and calibration procedure;
- same safety boundary and recovery definition;
- no mid-test retuning unless the dataset is split and clearly labelled.

If a retune is necessary, stop the dataset and start a new clearly named batch. Do not mix pre-retune and post-retune trials under one summary.

## Statistical Analysis

### Success/Failure Metrics

For pass counts such as 10/10, 19/20 or 5/5, report:

- observed success rate;
- Wilson 95% confidence interval;
- number of failed/protected trials;
- short interpretation.

Important wording:

> A 20/20 result should be interpreted as no observed failure in this small test set, not as proof of 100% reliability.

This wording is strict and helps avoid overclaiming.

### Continuous Metrics

For response metric, settling time, peak pitch and maximum wheel speed, report:

- mean;
- standard deviation;
- median;
- min/max;
- bootstrap 95% confidence interval for the mean;
- optionally interquartile range.

The main report can still show compact mean values. The appendix should hold the fuller table.

### E9 Comparative Statistics

For FULL vs FIXED_LQR:

- difference in mean response metric;
- difference in mean peak pitch;
- percentage improvement;
- bootstrap 95% CI for the mean difference;
- non-parametric effect size, preferably Cliff's delta;
- optional Mann-Whitney U p-value, but do not rely on p-value language because n is still small.

Recommended interpretation:

> Because the physical disturbance was manually applied and the sample size remains modest, the comparison is interpreted as small-sample engineering evidence with uncertainty, not as a formal proof of optimal control.

This keeps the claim defensible even if the confidence interval is wide.

## Report Integration

### Main Text

Keep the main body compact. Do not add a new long statistical methods section unless page space is cut elsewhere.

Recommended main-body changes:

- Replace E2 and E9 summary numbers with updated 20-trial values.
- Add one sentence after the E2 table:
  - "Trial-level spread and Wilson confidence intervals are retained in Appendix G."
- Add one sentence after the E9 table:
  - "The FULL/FIXED_LQR comparison is reported with bootstrap confidence intervals and effect-size statistics in Appendix G because the physical disturbance is manually applied."

Avoid adding more than 4-6 lines to the main body unless another section is shortened.

### Appendix G

Add a new subsection:

```text
Appendix G.X Small-sample statistical summaries
```

Include:

- E2 success-rate table with Wilson CI;
- E2 continuous-metric summary table;
- E9 success-rate table with Wilson CI;
- E9 FULL vs FIXED_LQR effect-size table;
- short note on manual disturbance limitations.

### Abstract

Update only if the new data materially changes headline results.

Examples:

- If E2 improves from 9/10 and 10/10 to 19/20 and 20/20, update the abstract.
- If E9 remains directionally supportive but with wide CI, keep the abstract concise and avoid confidence interval details there.

## Data and File Management

Do not overwrite current final datasets. Add new files with a new date stamp, for example:

```text
Report/appendices/E_data/E2_disturbance_recovery/recovery_trials_2026-04-26_extra.csv
Report/appendices/E_data/E2_disturbance_recovery/recovery_summary_2026-04-26_combined.csv
Report/appendices/E_data/E9_controller_ablation/ablation_trials_2026-04-26_extra.csv
Report/appendices/E_data/E9_controller_ablation/ablation_summary_2026-04-26_combined.csv
Report/appendices/E_data/statistical_summary_2026-04-26.md
```

The current 2026-04-24 datasets should remain available for traceability.

## Decision Gates

### Continue and update the report if:

- E2 added trials are broadly consistent with the current result;
- E9 FULL remains better than FIXED_LQR on response metric or peak pitch;
- no new safety issue appears;
- the added data does not force a major rewrite.

### Still update, but with careful wording, if:

- FULL still trends better but confidence intervals overlap;
- one or two additional failures occur;
- manual disturbance variability is visible.

In this case, frame the evidence as "directionally supportive small-sample engineering evidence".

### Do not over-expand the report if:

- the new results are noisy or contradictory;
- the robot hardware condition changes during testing;
- controller retuning is required halfway through;
- the page limit would be breached.

If this happens, use the current report wording and mention the new tests only in notes or future work.

## Page-Budget Strategy

The report is already close to the 35-page main-body limit. Any new statistical content should mainly go into Appendix G.

If main-body space is needed, shorten:

- general background in Chapter 2;
- broad explanation of common robotics concepts;
- repeated descriptions of WiFi/vision being supervisory;
- any sentence that repeats a table value without interpreting it.

Do not cut:

- objective-to-evidence mapping;
- E8 outlier caveat;
- E9 comparison interpretation;
- O3 arbitration evidence;
- repository evidence appendix.

## Expected Marking Benefit

This upgrade improves:

- objectivity;
- evidence traceability;
- baseline credibility;
- critical analysis;
- 80+ plausibility.

It does not fully remove the limitation that the robot experiments are manually disturbed and small-scale. The realistic target is to move the report from "credible 80 candidate" toward "more defensible 80+ candidate", not to make 80+ guaranteed.

## Minimal Checklist

- [ ] Add 10 E9 FULL trials.
- [ ] Add 10 E9 FIXED_LQR trials.
- [ ] Add 10 E2 forward trials.
- [ ] Add 10 E2 backward trials.
- [ ] Keep all failed/protected trials.
- [ ] Generate Wilson confidence intervals for pass/fail results.
- [ ] Generate mean/std/median/min/max for continuous metrics.
- [ ] Generate bootstrap confidence intervals for E9 differences.
- [ ] Add Appendix G statistical summary.
- [ ] Update E2/E9 main-text tables only if values changed.
- [ ] Rebuild `Report/main.pdf`.
- [ ] Recheck body page count before submission.
