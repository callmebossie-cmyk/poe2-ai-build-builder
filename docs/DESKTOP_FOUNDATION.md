# Desktop Foundation

Checkpoint 6A establishes a runnable React, TypeScript, and Tauri 2 shell under `desktop/`.

## First-run contract

The default provider is `none`. A user may finish onboarding without AI and reach the local-core dashboard. The selectable provider kinds are:

- `none` — deterministic features only.
- `ollama` — local endpoint and model, with no credential.
- `cloud` — user-selected endpoint and model; credential entry is intentionally deferred until OS secure storage is implemented.

Only non-secret provider metadata is stored in browser storage. The versioned configuration forces `credentialConfigured` to `false`, rejects unknown providers and quality modes, and safely resets malformed or incompatible state.

## Security boundary

- No API key field exists in Checkpoint 6A.
- No secret is written to `localStorage`, a JSON config file, source control, or the application bundle.
- The Tauri capability grants only `core:default`; filesystem and shell access are not enabled.
- The desktop Content layer is not a source of truth for game rules. Database, graph, calculator, and validator ownership remains local and deterministic.

## Validation

- Provider configuration: five Vitest tests.
- Frontend: strict TypeScript and Vite production build.
- Native shell: `cargo check` and Tauri release compilation with `--no-bundle`.
- Existing Python core: forty-two tests remain passing.

The generated executable and build directories are ignored. Installer/bundling belongs to Checkpoint 7.
