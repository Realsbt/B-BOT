# Project Management PDF Companion Exports

These PDFs are marker-readable companion exports for the management appendices.
The editable Office/Markdown source files remain the authoritative evidence.

They were generated with:

```bash
python3 Report/appendices/Project_management/pdf_exports/build_management_pdf_exports.py
```

## Generated Files

| Appendix | PDF companion export | Source evidence |
| --- | --- | --- |
| Appendix B | `Appendix_B_Project_Plan_Gantt_companion.pdf` | `Appendix_B_Project_Plan_Gantt/Project Planning Template - B-BOT filled.xlsx`, `Report/planning/Project_Management_Gantt_and_Weekly_Log.md`, `Report/figures/project_management_gantt.*` |
| Appendix C | `Appendix_C_Project_Risk_Register_companion.pdf` | `Appendix_C_Project_Risk_Register/Project Risk Register - B-BOT filled.docx` |
| Appendix D | `Appendix_D_CPD_Log_companion.pdf` | `Appendix_D_CPD_Log/CPD Log - B-BOT filled.docx` |
| Appendix E | `Appendix_E_Health_and_Safety_companion.pdf` | `Appendix_E_Health_and_Safety/H&S Risk Register - B-BOT filled.docx` |

## Export Note

LibreOffice, Microsoft Office and Pandoc are not installed in the current local
toolchain, so these are not pixel-exact Office exports. They are fixed-layout
PDF companion summaries generated from the same appendix evidence so that the
submission package does not rely only on editable `.docx` or `.xlsx` files.
