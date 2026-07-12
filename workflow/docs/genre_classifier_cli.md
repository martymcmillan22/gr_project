# Genre Classifier CLI
Document ID: BTPE-GENRE-CLI-001
Version: v1.0
Status: Active

---

## 1. Commands

- python3 workflow/cli.py genre-classifier "input text"
- python3 workflow/cli.py genre-classifier --input-file /path/to/input.txt
- python3 workflow/cli.py genre-classifier --stdin
- python3 workflow/cli.py genre-classifier --debug "input text"
- python3 workflow/cli.py genre-classifier --introspect "input text"

## 2. Behavior

The command executes in deterministic order:

1. Parse input from text, file, or stdin.
2. Run Strict Mode to build a validated QPU.
3. Run Genre Classifier on the validated QPU.
4. Print classification output and optional debug/introspection artifacts.

## 3. Output Fields

- genre
- confidence
- signals_used
- semantic_summary
