# Synthetic analyzer fixture

`framebudget demo --synthetic --out reports/demo` deterministically generates
two five-run suites. Candidate measurement intervals are 3 ms slower; this is
an analyzer and report fixture, not a Godot measurement. The generator lives in
`src/framebudget/synthetic.py`, and the controlled slowdown gate is tested in
`tests/unit/test_schema_compare.py`.
