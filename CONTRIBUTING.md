# Contributing

FrameBudget is a small, offline benchmark kit. Keep the Python runtime on the
standard library and keep changes testable without Godot whenever possible.

1. Use Python 3.11+ and install with `python -m pip install -e .`.
2. Install the optional lint tool with `python -m pip install -r requirements-dev.lock`.
3. Run `python -m unittest discover -s tests -p "test_*.py" -v` and `ruff check .`.
4. If Godot 4.7.2 is installed, set `GODOT_PATH` to its executable and run the
   same tests to include the headless smoke. Record any rendered experiments
   separately with their full manifest and raw CSV.

Please include a failure case for schema, process lifecycle, or compatibility
changes. Never present synthetic or headless data as rendered performance.
Open a small issue before adding a new dependency or a universal project plugin.
