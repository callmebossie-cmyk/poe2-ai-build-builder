# PoE2 AI Build Builder

Desktop build-planning tool for Path of Exile 2. The application will combine real local game data, deterministic graph/calculation/validation code, and AI-assisted theorycrafting.

## Current status

Checkpoints 1 through 5 are complete: real-data import, passive graph, candidate retrieval, live AI build directions, a live Full Build, and deterministic bounded validation. The Core MVP labels uncalculated qualitative/resource claims as advisory. Checkpoint 6 will add a provider-neutral desktop application with first-run provider selection. Downloaded data, generated databases, and live AI evidence are ignored by Git.

## Data proof of concept

Python 3.10 or newer is required. No runtime package dependency is needed.

```powershell
$env:PYTHONPATH = 'src'
python -m poe2_builder.cli fetch
python -m poe2_builder.cli build
python -m poe2_builder.cli validate
python -m poe2_builder.cli snipe
python -m poe2_builder.cli graph-demo --class-name Ranger
python -m poe2_builder.cli retrieve --skill Snipe --playstyle Fast --goal Mapping --budget Cheap
python -m poe2_builder.cli directions-contract-demo
python -m poe2_builder.cli directions-ollama --model qwen3:8b --output .cache/live-directions.json
python -m poe2_builder.cli full-build-ollama --model qwen3:8b --direction-id direction_2 --output .cache/live-full-build.json
```

Run the unit tests with:

```powershell
$env:PYTHONPATH = 'src'
python -m unittest discover -s tests -v
```

Desktop foundation commands:

```powershell
Set-Location desktop
npm install
npm test
npm run build
npm run tauri build -- --no-bundle
```

Read these files before continuing:

- `poe2_ai_build_builder_plan.md` — complete product and implementation plan
- `CHECKPOINT.md` — concise resume point
- `docs/DEVELOPMENT_STATUS.md` — detailed project state
- `TODO.md` — current task list
- `USER_ACTION_REQUIRED.md` — user-only actions and blockers
- `docs/DATA_SOURCES.md` — pinned provenance and distribution boundary
- `docs/DESKTOP_FOUNDATION.md` — provider-neutral first-run and desktop security boundary

## Working rule

Work one checkpoint at a time. Use real sourced data, record provenance and versions, run the relevant tests, update the state documents, and create a local commit. Push only when the user explicitly asks.
