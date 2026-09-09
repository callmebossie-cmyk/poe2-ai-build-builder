import { describe, expect, it } from "vitest";
import {
  DEFAULT_PROVIDER_CONFIG,
  configForProvider,
  parseStoredConfig,
  validateProviderConfig,
} from "./providerConfig";

describe("provider configuration", () => {
  it("starts disconnected so deterministic features remain available", () => {
    expect(DEFAULT_PROVIDER_CONFIG.provider).toBe("none");
    expect(DEFAULT_PROVIDER_CONFIG.onboardingComplete).toBe(false);
    const disconnected = { ...DEFAULT_PROVIDER_CONFIG, onboardingComplete: true };
    expect(validateProviderConfig(disconnected)).toEqual([]);
  });

  it("supplies local defaults without storing a credential", () => {
    const config = configForProvider("ollama");
    expect(config.endpoint).toBe("http://127.0.0.1:11434");
    expect(config.model).toBe("qwen3:8b");
    expect(config.credentialConfigured).toBe(false);
  });

  it("requires explicit cloud endpoint and model", () => {
    expect(validateProviderConfig(configForProvider("cloud"))).toEqual([
      "Provider endpoint is required.",
      "Provider model is required.",
    ]);
  });

  it("falls back safely for malformed or unknown persisted state", () => {
    expect(parseStoredConfig("not json")).toEqual(DEFAULT_PROVIDER_CONFIG);
    expect(parseStoredConfig('{"provider":"invented"}')).toEqual(DEFAULT_PROVIDER_CONFIG);
    expect(parseStoredConfig('{"schemaVersion":2,"provider":"none"}')).toEqual(DEFAULT_PROVIDER_CONFIG);
    expect(parseStoredConfig('{"schemaVersion":1,"provider":"none","qualityMode":"turbo"}')).toEqual(
      DEFAULT_PROVIDER_CONFIG,
    );
  });

  it("never restores credential state from ordinary storage", () => {
    const restored = parseStoredConfig(
      JSON.stringify({ ...configForProvider("ollama"), credentialConfigured: true }),
    );
    expect(restored.credentialConfigured).toBe(false);
  });
});
