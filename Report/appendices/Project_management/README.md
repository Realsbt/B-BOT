# Project Management Appendix Folder

This folder keeps the management evidence separated by the appendix order used in the report.

## Folder Map

| Folder | Report use | Current status |
| --- | --- | --- |
| `00_requirements/` | Requirement notes supplied with the templates | CPD requirement text stored here |
| `Appendix_A_Preliminary_Proposal/` | Appendix A: preliminary project proposal | Proposal PDF added |
| `Appendix_B_Project_Plan_Gantt/` | Appendix B: project plan and Gantt chart | Filled planning spreadsheet added; Gantt source and rendered figures are referenced below |
| `Appendix_C_Project_Risk_Register/` | Appendix C: project-delivery risk register | Filled project risk register added in Markdown and Word format |
| `Appendix_D_CPD_Log/` | Appendix D: CPD log | Filled CPD log added |
| `Appendix_E_Health_and_Safety/` | Appendix E: health and safety risk assessment | Filled H&S risk register added |
| `pdf_exports/` | Marker-readable companion PDFs for Appendices B-E | Generated PDF companion exports added |
| `source_templates/` | Original blank templates | Original blank templates stored here for reference |

## External Project Management Files

The reconstructed weekly log and Gantt source remain outside this folder so the existing report workflow does not break:

- Weekly log and Gantt notes: `Report/planning/Project_Management_Gantt_and_Weekly_Log.md`
- Gantt render script: `Report/planning/render_project_gantt.py`
- Rendered Gantt PDF: `Report/figures/project_management_gantt.pdf`
- Rendered Gantt PNG: `Report/figures/project_management_gantt.png`

## PDF Companion Exports

The table-heavy management appendices also have fixed-layout PDF companion exports in `pdf_exports/`:

- `Appendix_B_Project_Plan_Gantt_companion.pdf`
- `Appendix_C_Project_Risk_Register_companion.pdf`
- `Appendix_D_CPD_Log_companion.pdf`
- `Appendix_E_Health_and_Safety_companion.pdf`

These are generated from the same source evidence using `pdf_exports/build_management_pdf_exports.py`. They are not pixel-exact Office exports because LibreOffice, Microsoft Office and Pandoc are not installed in the local toolchain.

## Distinction Between Risk Files

Appendix C should discuss project-delivery risk: schedule, integration, testing, data quality, scope and backup/version control.

Appendix E should discuss health and safety risk: high-torque motors, robot falling, battery/wiring faults, soldering, sharp parts, cables and unexpected motion during wireless or vision testing.
