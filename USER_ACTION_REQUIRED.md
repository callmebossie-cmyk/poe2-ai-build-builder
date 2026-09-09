# USER ACTION REQUIRED

## Live AI provider for Checkpoint 4B

Status: BLOCKED

Why:

Checkpoint 4 requires at least one live AI provider run. Choosing a cloud provider can create API cost and requires a user-owned credential; choosing Ollama requires selecting and downloading a local model. Ollama 0.33.3 is installed, but no local models are currently installed.

Choose one route:

1. Cloud provider: name the provider/model and acceptable test budget. Configure its key through the provider's secure local environment or credential mechanism. Do not paste or commit the secret into this repository.
2. Local Ollama: name or approve a model to download and confirm that using the required disk space and compute is acceptable.

Return to the agent with either:

- `Use cloud provider: <provider/model>, test budget <amount>`
- `Use Ollama: <model>`

Blocked work:

- Live provider adapter and live structured-output run for Checkpoint 4B.

Unblocked work already completed:

- Provider-neutral request/response contract, quality modes, offline contract provider, schema validation, entity-reference validation, and tests.

When a task genuinely requires account ownership, OAuth approval, an API key, license permission, paid action, or an inaccessible OS prompt, document the exact steps here without committing secrets.
