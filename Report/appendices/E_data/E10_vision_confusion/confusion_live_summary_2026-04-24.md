# E10 Live Gesture Confusion Summary

Date: 2026-04-24 CST

This summary keeps all live trials in the audit table, then selects the latest clean pass for each gesture for the clean confusion matrix.

## Key Results

- Live trials recorded: 9
- Clean gestures available: 6 / 6
- Clean selected frames: 259
- Overall clean frame-label accuracy: 0.853

## Audit Status Counts

- fail_false_command: 1
- fail_no_stable_expected: 1
- mixed_false_command: 1
- pass_clean: 6

## Selected Clean Trials

- NoHand: `live_01_nohand`, frame accuracy 1.000, primary command `None/stop`
- Zero: `live_03_zero_centered`, frame accuracy 0.537, primary command `DRIVE,0,0`
- Five: `live_04_five_centered`, frame accuracy 0.804, primary command `DRIVE,250,0`
- PointLeft: `live_07_pointleft_image_left_clean`, frame accuracy 1.000, primary command `DRIVE,0,600`
- PointRight: `live_08_pointright_image_right_clean`, frame accuracy 1.000, primary command `DRIVE,0,-600`
- Thumb_up: `live_09_thumb_up_clean`, frame accuracy 0.792, primary command `JUMP`

## Generated Files

- `Report/appendices/E_data/E10_vision_confusion/confusion_trials_live_audit_2026-04-24.csv`
- `Report/appendices/E_data/E10_vision_confusion/confusion_command_matrix_live_clean_2026-04-24.csv`
- `Report/appendices/E_data/E10_vision_confusion/confusion_frame_label_matrix_live_clean_2026-04-24.csv`
- `Report/figures/e10_vision_confusion_live_2026-04-24.png`

Notes:

- `live_02_zero` is retained as a false forward-command risk caused by poor closed-fist pose/lighting.
- `live_05_pointleft` is retained as a failed pointing-label trial before the rule relaxation.
- `live_06_pointleft` is retained as an operator pose error / mixed false-direction command trial; its sample image points image-right.
- `Thumb_up` maps to `JUMP` in the encoder, but the live robot bridge blocks stunt commands unless `stunt_armed=true`.
