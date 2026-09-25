1. Progress
Generic repeat-driven expression tool implemented and working at expression_tools/parse_table_row/. Your core hypothesis holds: a <repeat> of (column name, column type) drives a fixed pool of slot outputs pruned by <filter>, so the workflow editor shows exactly one connection point per configured column.

2. Files (all new unless marked)
- expression_tools/parse_table_row/parse_table_row.xml — repeat input, hardened ECMA-5.1 expression, 15 tests
- expression_tools/parse_table_row/macros.xml — typed_output/typed_outputs slot-pool macro + @MAX_SLOTS@
- expression_tools/parse_table_row/.shed.yml — so ToolShed/CI treat it as a repository
- expression_tools/parse_table_row/test-data/ — mixed.csv, mixed.tsv, bad_values.csv, header_only.csv, wide.csv
- Makefile (modified, 2 lines) — TOOL_DIRS now also globs expression_tools/*/; without this make lint/make test silently skipped the new dir. CI needs no change (it uses the planemo changed-file list, and paths-ignore doesn't cover expression_tools/**).

3. Key decisions
- 10 slots × 4 types = 40 declared outputs; ceiling single-sourced from @MAX_SLOTS@ (verified tokens expand inside <expression> and <help>).
- Errors via __error_message, not throw; strict numeric regex (not parseFloat/Number, which accept 3.1xyz, ""→0, 1e400→null); booleans accept true/false/yes/no/1/0 any case instead of silently yielding false.
- Output labels are Cheetah ($columns[0]['column_name']), not Jinja.

4. Verified
15/15 tests passed at the last completed planemo test; planemo lint --fail_level warn clean; XSD-valid against both Galaxy's and planemo's schemas; help RST clean; editor-time filter/label behaviour checked directly against filter_output/get_all_outputs.