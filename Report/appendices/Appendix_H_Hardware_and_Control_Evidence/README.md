# Appendix H - Hardware and Control Modelling Evidence

This appendix folder stores supporting evidence for the custom hardware and control-modelling parts of B-BOT.

## Files

| File | Type | Use in the report |
| --- | --- | --- |
| `PCB_Schematic.png` | PCB schematic export image | Evidence that the ESP32 controller electronics were designed for this robot, including IMU, motor-interface, expansion and power-management paths. |
| `PCB_Layout.png` | PCB layout export image | Evidence of the physical custom controller-board layout. |
| `Dynamics_Modelling.pdf` | Original modelling derivation notes by Botao Su, 9 pages | Supporting dynamics/modelling material for the wheel-legged inverted-pendulum control discussion. |
| `LQR_Control_Algorithm.pdf` | Original control derivation notes by Botao Su, 6 pages | Supporting LQR/VMC algorithm material for the control architecture discussion. |

## Report Integration

- Chapter 3 should only summarise the design decisions: custom ESP32 PCB, six motor interfaces, IMU path, expansion interface, power management, leg-length-dependent LQR and VMC torque mapping.
- Full PCB images belong in Appendix H rather than the main body, because the report is already close to the 35-page body limit.
- The two modelling/control PDFs are original derivation notes by Botao Su and are retained as supporting appendix evidence rather than reproduced in full in the main report.

## Metadata Note

The two PDF files were originally exported on another computer and previously carried incorrect embedded author metadata. The PDF document information has been rewritten so that `pdfinfo` reports `Botao Su` as the author. The content is treated as original B-BOT modelling and control derivation evidence.
