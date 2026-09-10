import { invoke, isTauri } from "@tauri-apps/api/core";
import { BuildDirection } from "./buildDirections";
import { RetrievalIntent } from "./candidateRetrieval";

export interface FullBuild {
  build_id: string;
  title: string;
  level: number;
  class_name: string;
  ascendancy_id: string;
  main_skill_id: string;
  attributes: { strength: number; dexterity: number; intelligence: number };
  passive_ids: string[];
  passive_direction: string;
  defense: string;
  resource_solution: string;
  leveling_concept: string;
  rotation: string;
  affix_priorities: string[];
  upgrade_order: string[];
  skill_links: Array<{ skill_id: string; support_ids: string[] }>;
  equipment: Array<{ slot: string; item_base_id: string; mod_ids: string[] }>;
}

export interface FullBuildResult {
  provider: { name: string; is_live_ai: boolean };
  build: FullBuild;
  validation: Record<string, boolean>;
  claim_boundaries: Record<string, unknown>;
  presentation: BuildPresentation;
}

export interface PassiveNodeDetail {
  id: string; name: string; x: number; y: number; stats: string[]; depth: number;
  is_start: boolean; is_target: boolean; is_notable: boolean; is_keystone: boolean;
  icon?: string; is_allocated?: boolean; ascendancy_id?: string | null;
}
export interface BuildPresentation {
  inspection: {
    nodes: PassiveNodeDetail[]; edges: Array<{ from: string; to: string }>;
    allocation_order: string[]; parents: Record<string, string | null>;
    ascendancy_name: string; warnings: string[];
    sources: Array<{ name: string; version: string; file_name: string; url: string }>;
    skill_effects: Array<{ name: string; text: string[]; levels: Record<string, Record<string, unknown>> }>;
    skill_levels: Record<string, Record<string, unknown>>;
  };
  passive_tree: { start_id: string; nodes: PassiveNodeDetail[]; edges: Array<{ from: string; to: string }> };
  skills: Array<{
    id: string; name: string; description: string; tags: string[];
    supports: Array<{ id: string; name: string; description: string; tags: string[]; crafting_level: number | null; relationship: string }>;
  }>;
  equipment: Array<{
    slot: string; base_id: string; name: string; item_class: string; drop_level: number;
    requirements: Record<string, number>; properties: Record<string, number>;
    mods: Array<{ id: string; name: string; generation_type: string; required_level: number; text: string }>;
  }>;
}

export interface ChatMessage { role: "user" | "assistant"; content: string }
export interface ChatAnswer { answer: string; grounded_entity_ids: string[]; advisory: boolean }

function coreDirection(direction: BuildDirection): Record<string, unknown> {
  return {
    direction_id: direction.directionId, title: direction.title, concept: direction.concept,
    class_name: direction.className, ascendancy_id: direction.ascendancyId, skill_id: direction.skillId,
    mechanic_ids: direction.mechanicIds, support_ids: direction.supportIds, passive_ids: direction.passiveIds,
    item_base_ids: direction.itemBaseIds, mod_ids: direction.modIds, unique_ids: direction.uniqueIds,
    damage_direction: direction.damageDirection, defense_direction: direction.defenseDirection,
    mapping_viability: direction.mappingViability, boss_viability: direction.bossViability,
    budget: direction.budget,
    league_start: { viable: direction.leagueStart.viable, rationale: direction.leagueStart.rationale },
    strengths: direction.strengths, weaknesses: direction.weaknesses,
    critical_dependencies: direction.criticalDependencies,
  };
}

export async function generateFullBuild(endpoint: string, model: string, direction: BuildDirection): Promise<FullBuildResult> {
  if (!isTauri()) throw new Error("Full Build generation is available in the native app.");
  return invoke<FullBuildResult>("generate_full_build", { request: { endpoint, model, direction: coreDirection(direction) } });
}

export async function askAboutBuild(endpoint: string, model: string, direction: BuildDirection,
  build: FullBuild, intent: RetrievalIntent, question: string, history: ChatMessage[]): Promise<ChatAnswer> {
  if (!isTauri()) throw new Error("Build chat is available in the native app.");
  return invoke<ChatAnswer>("answer_build_question", {
    request: { endpoint, model, direction: coreDirection(direction), build, intent, question, history: history.slice(-12) },
  });
}
