import { invoke, isTauri } from "@tauri-apps/api/core";

export interface CoreStatus {
  validationChecks: number;
  passedChecks: number;
  snipeSkills: number;
  passiveNodes: number;
  bowBases: number;
  provenanceFiles: number;
}

export async function readCoreStatus(): Promise<CoreStatus> {
  if (!isTauri()) {
    throw new Error("The deterministic core bridge is available in the native app.");
  }
  return invoke<CoreStatus>("core_status");
}
