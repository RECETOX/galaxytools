1. Progress
Generic repeat-driven expression tool implemented and working at expression_tools/parse_table_row/. Your core hypothesis holds: a <repeat> drives a fixed pool of slot outputs pruned by <filter>, so the workflow editor shows exactly one connection point per configured column. Slots are assigned to table columns **by position** (slot 1 = column 1); the repeat configures only each column's type, not its name.

2. Files (all new unless marked)
- expression_tools/parse_table_row/parse_table_row.xml — repeat input, hardened ECMA-5.1 expression, 15 tests
- expression_tools/parse_table_row/macros.xml — typed_output/typed_outputs slot-pool macro + @MAX_SLOTS@
- expression_tools/parse_table_row/.shed.yml — so ToolShed/CI treat it as a repository
- expression_tools/parse_table_row/test-data/ — mixed.csv, mixed.tsv, bad_values.csv, header_only.csv, wide.csv
- Makefile (modified, 2 lines) — TOOL_DIRS now also globs expression_tools/*/; without this make lint/make test silently skipped the new dir. CI needs no change (it uses the planemo changed-file list, and paths-ignore doesn't cover expression_tools/**).

3. Key decisions
- Columns matched by position, not name (slot i = column i); the repeat holds only column_type. Configure fewer entries than the table has columns to use part of a table. The header is still read, only to name columns in error messages.
- 10 slots × 4 types = 40 declared outputs; ceiling single-sourced from @MAX_SLOTS@ (verified tokens expand inside <expression> and <help>).
- Errors via __error_message, not throw; strict numeric regex (not parseFloat/Number, which accept 3.1xyz, ""→0, 1e400→null); booleans accept true/false/yes/no/1/0 any case instead of silently yielding false.
- Output labels are now static text ("column 1 (float)"). Labels are Cheetah, not Jinja, and a label that raises fails the job — so nothing in a label may index the repeat.

4. Verified
15/15 tests passed at the last completed planemo test; planemo lint --fail_level warn clean; XSD-valid against both Galaxy's and planemo's schemas; help RST clean; editor-time filter/label behaviour checked directly against filter_output/get_all_outputs.