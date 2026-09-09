# PoE2 AI Build Builder

Desktop build-planning tool for Path of Exile 2. The application will combine real local game data, deterministic graph/calculation/validation code, and AI-assisted theorycrafting.

## Current status

Checkpoint 1 implements a real-data Snipe import pipeline. It downloads pinned GGG/RePoE exports locally, verifies checksums, builds a normalized SQLite database, and validates the checkpoint acceptance criteria. Downloaded data and generated databases are ignored by Git.

## Data proof of concept

Python 3.10 or newer is required. No runtime package dependency is needed.

```powershell
$env:PYTHONPATH = 'src'
python -m poe2_builder.cli fetch
python -m poe2_builder.cli build
python -m poe2_builder.cli validate
python -m poe2_builder.cli snipe
```

Run the unit tests with:

```powershell
$env:PYTHONPATH = 'src'
python -m unittest discover -s tests -v
```

Read these files before continuing:

- `poe2_ai_build_builder_plan.md` — complete product and implementation plan
- `CHECKPOINT.md` — concise resume point
- `docs/DEVELOPMENT_STATUS.md` — detailed project state
- `TODO.md` — current task list
- `USER_ACTION_REQUIRED.md` — user-only actions and blockers
- `docs/DATA_SOURCES.md` — pinned provenance and distribution boundary

## Working rule

Work one checkpoint at a time. Use real sourced data, record provenance and versions, run the relevant tests, update the state documents, then commit and push.
