# E10 Vision Confusion Matrix

Date/time: 2026-04-24 08:23 CST
Operator: user + Codex
Firmware commit: 70c3b17
Controller mode: dry-run vision bridge, `mode=gesture`, `dry_run=true`, `debug_events=true`
Hardware state: ESP32-CAM powered and connected to micro-ROS Agent; robot drive commands not sent because bridge was in dry-run mode.
Environment: bench/lab setup, lighting not formally controlled, camera distance not formally measured in pilot.
Trial list: see `confusion_trials_pilot_2026-04-24.csv`
Safety notes: dry-run mode used; observed commands were log outputs only.

Files:

- `camera_smoke_2026-04-24.csv`
- `confusion_trials_pilot_2026-04-24.csv`
- `confusion_trials_after_patch_2026-04-24.csv`
- `frame_check_2026-04-24.jpg`
- `frame_check_five_2026-04-24.jpg`
- `frame_check_pointleft_2026-04-24.jpg`
- `plots/`

Pilot interpretation:

- Five and Zero reached stable labels and generated the expected dry-run commands.
- PointLeft failed in both attempts; one retest produced a false stable Five, causing a false forward command in dry-run logs.
- Thumb_up was detected only once as an unstable instantaneous label and did not generate JUMP.
- NoHand / frame absence triggered the expected safety stop path (`QUEUE_STOP` and `DRIVE,0,0`).

This pilot should be reported as baseline evidence, not as the final N=10 confusion matrix.

Patch/test notes:

- A saved image initially showed the camera pointing at the ceiling/light, explaining the unstable first retest.
- After physically aiming the camera at the hand, Five passed again.
- The classifier was patched to use horizontal index-finger geometry for PointLeft/PointRight and to guard all stunt commands with `stunt_armed`.
- PointLeft improved from no directional labels to intermittent PointLeft labels in one run, but did not reach a stable command. A later saved PointLeft frame showed a clear side-on pointing pose, yet the bridge still logged `None`, so the limitation is likely MediaPipe landmark robustness at low resolution/lighting.
- Default `debounce_frames` was changed from 5 to 3 because the camera runs at only about 6 Hz.
