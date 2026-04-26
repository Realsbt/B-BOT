# Presentation Folder

This folder contains the presentation materials for the B-BOT final presentation.

## Files

- `B-BOT_final_presentation.pptx` — PowerPoint deck for a 20-25 minute presentation.
- `presentation_script.md` — bilingual slide-by-slide timing, demo plan and speaker script.
- `qa_preparation.md` — bilingual likely Q&A topics and prepared answers.
- `make_presentation.py` — local generator script used to build the PPTX.
- `.deps/` — local Python dependencies installed for generating the PPTX.

## Suggested Use

1. Rehearse with `presentation_script.md`.
2. Keep the live demonstration conservative.
3. Use `qa_preparation.md` to practise short answers.
4. If the PPTX needs regenerating, run:

```bash
PYTHONPATH=Report/presentation/.deps python3 Report/presentation/make_presentation.py
```

The deck uses existing report figures and does not introduce new experimental claims.
