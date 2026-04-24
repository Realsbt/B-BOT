# Report Appendices Index

This folder contains appendix evidence for the final report.

## Required Handbook Items

| Report appendix | Required item | Current location | Status |
| --- | --- | --- | --- |
| Appendix A | Preliminary Project Proposal | `Project_management/Appendix_A_Preliminary_Proposal/` | Added |
| Appendix B | Project Plan and Gantt Chart | `Project_management/Appendix_B_Project_Plan_Gantt/`, `Report/planning/Project_Management_Gantt_and_Weekly_Log.md`, `Report/figures/project_management_gantt.*`, `Project_management/pdf_exports/` | Added; LaTeX summary and PDF companion export completed |
| Appendix C | Risk Register | `Project_management/Appendix_C_Project_Risk_Register/`, `Project_management/pdf_exports/` | Draft completed; PDF companion export completed |
| Appendix D | CPD Log | `Project_management/Appendix_D_CPD_Log/`, `Project_management/pdf_exports/` | Draft completed; PDF companion export completed |
| Appendix E | Health & Safety Risk Assessment | `Project_management/Appendix_E_Health_and_Safety/`, `Project_management/pdf_exports/` | Draft completed; PDF companion export completed |
| Appendix F | Software repository link and README evidence | `Appendix_F_Software_Repository/` | Draft completed; final commit/tag and public access still need confirmation |

## Additional Supporting Evidence

| Report appendix | Item | Current location | Status |
| --- | --- | --- | --- |
| Appendix G | Experiment data, logs and extra validation evidence | `E_data/` | Data index added; measured/provisional status documented |

## Remaining Integration Work

- The appendices are now referenced from `Report/main.tex`; final submission still needs a last consistency pass after all hardware data are replaced.
- Replace provisional physical datasets before final submission where possible.
- Update Appendix F with the final commit hash or release tag.
- Confirm no private credentials are present in tracked files before making the repository public.

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

LibreOffice/soffice, Microsoft Office and Pandoc are not currently available on this machine. The `Project_management/pdf_exports/` files are therefore fixed-layout companion exports generated from the appendix evidence, not pixel-exact Office exports. Exact Office visual exports can still be regenerated later through Word, Excel or LibreOffice if required.
