export const PROVIDER_CONFIG_KEY = "poe2-builder.provider-config.v1";

export type ProviderKind = "none" | "ollama" | "cloud";
export type QualityMode = "economy" | "balanced" | "deep_analysis" | "maximum";

export interface ProviderConfig {
  schemaVersion: 1;
  provider: ProviderKind;
  endpoint: string;
  model: string;
  qualityMode: QualityMode;
  credentialConfigured: false;
  onboardingComplete: boolean;
}

export const DEFAULT_PROVIDER_CONFIG: ProviderConfig = {
  schemaVersion: 1,
  provider: "none",
  endpoint: "",
  model: "",
  qualityMode: "balanced",
  credentialConfigured: false,
  onboardingComplete: false,
};

const providerDefaults: Record<ProviderKind, Pick<ProviderConfig, "endpoint" | "model">> = {
  none: { endpoint: "", model: "" },
  ollama: { endpoint: "http://127.0.0.1:11434", model: "qwen3:8b" },
  cloud: { endpoint: "", model: "" },
};

export function configForProvider(provider: ProviderKind, current = DEFAULT_PROVIDER_CONFIG): ProviderConfig {
  const defaults = providerDefaults[provider];
  return { ...current, provider, ...defaults, credentialConfigured: false };
}

export function validateProviderConfig(config: ProviderConfig): string[] {
  const errors: string[] = [];
  const qualityModes: QualityMode[] = ["economy", "balanced", "deep_analysis", "maximum"];
  if (config.schemaVersion !== 1) errors.push("Unsupported provider configuration version.");
  if (config.provider !== "none" && !config.endpoint.trim()) errors.push("Provider endpoint is required.");
  if (config.provider !== "none" && !config.model.trim()) errors.push("Provider model is required.");
  if (!qualityModes.includes(config.qualityMode)) errors.push("Unknown quality mode.");
  if (config.credentialConfigured !== false) errors.push("Secrets cannot be stored in provider configuration.");
  return errors;
}

export function parseStoredConfig(raw: string | null): ProviderConfig {
  if (!raw) return DEFAULT_PROVIDER_CONFIG;
  try {
    const value = JSON.parse(raw) as Partial<ProviderConfig>;
    const provider = value.provider;
    if (value.schemaVersion !== 1 || (provider !== "none" && provider !== "ollama" && provider !== "cloud")) {
      return DEFAULT_PROVIDER_CONFIG;
    }
    const candidate: ProviderConfig = {
      ...DEFAULT_PROVIDER_CONFIG,
      ...value,
      schemaVersion: 1,
      provider,
      credentialConfigured: false,
    };
    return validateProviderConfig(candidate).length ? DEFAULT_PROVIDER_CONFIG : candidate;
  } catch {
    return DEFAULT_PROVIDER_CONFIG;
  }
}
