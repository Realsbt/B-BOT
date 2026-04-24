# Provisional Data Policy

These files are layout and analysis placeholders only.

Do not move any value from a `provisional_*.csv` or `synthetic_*.csv` file into the final report unless it has been replaced by measured data.

Required replacement rule:

- Keep the file structure and column names.
- Replace provisional rows with measured rows.
- Remove `provisional=true`.
- Remove `source=synthetic_planning_placeholder_not_measured`.
- Update the experiment README with date, hardware state, and exclusion notes.

Final check:

```bash
rg "provisional=true|provisional=True|synthetic_planning_placeholder_not_measured|PROVISIONAL" Report
```
