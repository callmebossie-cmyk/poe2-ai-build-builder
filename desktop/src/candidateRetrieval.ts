import { invoke, isTauri } from "@tauri-apps/api/core";

export interface RetrievalIntent {
  skill: "Snipe";
  playstyle: "Fast" | "Balanced" | "Defensive";
  goal: "Mapping" | "Bossing" | "Hybrid";
  budget: "Cheap" | "Medium" | "Expensive";
}

export interface CandidatePreview {
  id: string;
  name: string;
  score: number;
  reasons: string[];
}

export interface CandidateGroup {
  category: string;
  count: number;
  top: CandidatePreview[];
}

export interface RetrievalSummary extends Omit<RetrievalIntent, "skill"> {
  skillName: string;
  serializedBytes: number;
  totalCandidates: number;
  groups: CandidateGroup[];
}

export const DEFAULT_INTENT: RetrievalIntent = {
  skill: "Snipe",
  playstyle: "Fast",
  goal: "Mapping",
  budget: "Cheap",
};

export async function retrieveCandidates(request: RetrievalIntent): Promise<RetrievalSummary> {
  if (!isTauri()) throw new Error("Candidate retrieval is available in the native app.");
  return invoke<RetrievalSummary>("retrieve_candidates", { request });
}
