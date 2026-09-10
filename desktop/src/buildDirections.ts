import { invoke, isTauri } from "@tauri-apps/api/core";
import { RetrievalIntent } from "./candidateRetrieval";
import { QualityMode } from "./providerConfig";

export interface Viability {
  rating: number;
  rationale: string;
}

export interface BuildDirection {
  directionId: string;
  title: string;
  concept: string;
  className: string;
  ascendancyId: string;
  skillId: string;
  mechanicIds: string[];
  supportIds: string[];
  passiveIds: string[];
  itemBaseIds: string[];
  modIds: string[];
  uniqueIds: string[];
  damageDirection: string;
  defenseDirection: string;
  mappingViability: Viability;
  bossViability: Viability;
  budget: string;
  leagueStart: { viable: boolean; rationale: string };
  strengths: string[];
  weaknesses: string[];
  criticalDependencies: string[];
}

export interface DirectionResult {
  providerName: string;
  qualityMode: QualityMode;
  attempts: number;
  requestBytes: number;
  directions: BuildDirection[];
}

export interface DirectionRequest extends RetrievalIntent {
  endpoint: string;
  model: string;
  qualityMode: QualityMode;
}

export async function generateDirections(request: DirectionRequest): Promise<DirectionResult> {
  if (!isTauri()) throw new Error("AI build directions are available in the native app.");
  return invoke<DirectionResult>("generate_directions", { request });
}
