# Report Appendices Index

This folder contains appendix evidence for the final report.

## Required Handbook Items

| Report appendix | Required item | Current location | Status |
| --- | --- | --- | --- |
| Appendix A | Preliminary Project Proposal | `Project_management/Appendix_A_Preliminary_Proposal/` | Added |
| Appendix B | Project Plan and Gantt Chart | `Project_management/Appendix_B_Project_Plan_Gantt/`, `Report/planning/Project_Management_Gantt_and_Weekly_Log.md`, `Report/figures/project_management_gantt.*`, `Project_management/pdf_exports/` | Added; LaTeX summary and PDF companion export completed |
| Appendix C | Risk Register | `Project_management/Appendix_C_Project_Risk_Register/`, `Project_management/pdf_exports/` | Final report evidence register completed; PDF companion export completed |
| Appendix D | CPD Log | `Project_management/Appendix_D_CPD_Log/`, `Project_management/pdf_exports/` | Completed; PDF companion export completed |
| Appendix E | Health & Safety Risk Assessment | `Project_management/Appendix_E_Health_and_Safety/`, `Project_management/pdf_exports/` | Completed; PDF companion export completed |
| Appendix F | Software repository link and README evidence | `Appendix_F_Software_Repository/` | Software evidence completed; submitted public repository commit is identified for marking |

## Additional Supporting Evidence

| Report appendix | Item | Current location | Status |
| --- | --- | --- | --- |
| Appendix G | Experiment data, logs and extra validation evidence | `E_data/` | Data index added; all E1--E11 datasets are measured |
| Appendix H | Hardware and control modelling evidence | `Appendix_H_Hardware_and_Control_Evidence/` | PCB schematic/layout added; original dynamics and LQR/VMC derivation notes added; PDF metadata corrected to Botao Su |

## Final Submission Checks

- The appendices are referenced from `Report/main.tex` and have a concise LaTeX summary in the final report.
- Freeze the submitted public repository state at the recorded commit.
- Confirm tracked credential files contain only template placeholders before submission.

## Export Format Policy

The final report PDF should remain the self-contained document that markers read first. Editable Office files are useful as source evidence, but table-heavy appendices should also have a marker-readable PDF export or a LaTeX summary inside `Report/main.tex`.

| Appendix | Source format | Recommended submission/export format | Reason |
| --- | --- | --- | --- |
| A Proposal | PDF | Keep PDF | Already marker-readable |
| B Project plan and Gantt | XLSX, Markdown, generated figure | Use the generated Gantt PDF/PNG in the report; keep `Project_management/pdf_exports/Appendix_B_Project_Plan_Gantt_companion.pdf` as a marker-readable companion | Spreadsheet is source evidence, but PDF is safer for layout |
| C Project risk register | DOCX and Markdown | Keep the key rows as a LaTeX table and include `Project_management/pdf_exports/Appendix_C_Project_Risk_Register_companion.pdf` | This is a formal management table and should not depend on the marker opening Word |
| D CPD log | DOCX | Include `Project_management/pdf_exports/Appendix_D_CPD_Log_companion.pdf` if external appendices are submitted | CPD is table-based and easier to check as fixed-layout PDF |
| E H&S risk assessment | DOCX | Include `Project_management/pdf_exports/Appendix_E_Health_and_Safety_companion.pdf` | Safety forms often depend on table layout and signatures/checkboxes |
| F Software evidence | Markdown | Keep Markdown as source; include concise LaTeX summary in the report | Text evidence does not need vector conversion |
| G Experiment data | CSV/logs, generated figures, screenshots | Keep CSV/logs raw; use PDF for generated line/bar plots when possible; keep camera images as PNG/JPEG | Raw data must stay auditable, while generated plots benefit from vector PDF |
| H Hardware/control evidence | PNG PCB exports and PDF modelling/control notes | Include PCB images and a concise evidence table in the report appendix; keep the original PDFs as external supporting evidence | PCB images are useful marker-facing evidence, while full modelling notes are too long for the main body |

LibreOffice/soffice, Microsoft Office and Pandoc are not currently available on this machine. The `Project_management/pdf_exports/` files are therefore fixed-layout companion exports generated from the appendix evidence, not pixel-exact Office exports. Exact Office visual exports can still be regenerated later through Word, Excel or LibreOffice if required.
