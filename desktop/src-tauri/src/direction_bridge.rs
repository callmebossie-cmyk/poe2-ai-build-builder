use crate::core_bridge::run_core_command;
use serde::{Deserialize, Serialize};
use serde_json::Value;

#[derive(Debug, Deserialize)]
#[serde(rename_all = "camelCase")]
pub struct DirectionRequest {
    skill: String,
    playstyle: String,
    goal: String,
    budget: String,
    endpoint: String,
    model: String,
    quality_mode: String,
}

#[derive(Debug, Serialize)]
#[serde(rename_all = "camelCase")]
pub struct Viability {
    rating: i64,
    rationale: String,
}

#[derive(Debug, Serialize)]
#[serde(rename_all = "camelCase")]
pub struct LeagueStart {
    viable: bool,
    rationale: String,
}

#[derive(Debug, Serialize)]
#[serde(rename_all = "camelCase")]
pub struct BuildDirection {
    direction_id: String,
    title: String,
    concept: String,
    class_name: String,
    ascendancy_id: String,
    skill_id: String,
    mechanic_ids: Vec<String>,
    support_ids: Vec<String>,
    passive_ids: Vec<String>,
    item_base_ids: Vec<String>,
    mod_ids: Vec<String>,
    unique_ids: Vec<String>,
    damage_direction: String,
    defense_direction: String,
    mapping_viability: Viability,
    boss_viability: Viability,
    budget: String,
    league_start: LeagueStart,
    strengths: Vec<String>,
    weaknesses: Vec<String>,
    critical_dependencies: Vec<String>,
}

#[derive(Debug, Serialize)]
#[serde(rename_all = "camelCase")]
pub struct DirectionResult {
    provider_name: String,
    quality_mode: String,
    attempts: i64,
    request_bytes: i64,
    directions: Vec<BuildDirection>,
}

fn choice(value: &str, allowed: &[&str], field: &str) -> Result<(), String> {
    if allowed.contains(&value) {
        Ok(())
    } else {
        Err(format!("Unsupported {field} value"))
    }
}

fn validate_request(request: &DirectionRequest) -> Result<(), String> {
    choice(&request.skill, &["Snipe"], "skill")?;
    choice(
        &request.playstyle,
        &["Fast", "Balanced", "Defensive"],
        "playstyle",
    )?;
    choice(&request.goal, &["Mapping", "Bossing", "Hybrid"], "goal")?;
    choice(&request.budget, &["Cheap", "Medium", "Expensive"], "budget")?;
    choice(
        &request.quality_mode,
        &["economy", "balanced", "deep_analysis", "maximum"],
        "quality mode",
    )?;
    if request.endpoint != "http://127.0.0.1:11434" && request.endpoint != "http://localhost:11434"
    {
        return Err("Only the local Ollama endpoint is supported".into());
    }
    if request.model.is_empty()
        || request.model.len() > 100
        || !request
            .model
            .chars()
            .all(|character| character.is_ascii_alphanumeric() || ".:_-/".contains(character))
    {
        return Err("Invalid Ollama model name".into());
    }
    Ok(())
}

fn text(value: &Value, field: &str) -> Result<String, String> {
    value
        .get(field)
        .and_then(Value::as_str)
        .map(String::from)
        .ok_or_else(|| format!("Direction output is missing {field}"))
}

fn texts(value: &Value, field: &str) -> Result<Vec<String>, String> {
    value
        .get(field)
        .and_then(Value::as_array)
        .ok_or_else(|| format!("Direction output is missing {field}"))?
        .iter()
        .map(|item| {
            item.as_str()
                .map(String::from)
                .ok_or_else(|| format!("Direction output contains malformed {field}"))
        })
        .collect()
}

fn viability(value: &Value, field: &str) -> Result<Viability, String> {
    let row = value
        .get(field)
        .ok_or_else(|| format!("Direction output is missing {field}"))?;
    Ok(Viability {
        rating: row
            .get("rating")
            .and_then(Value::as_i64)
            .ok_or_else(|| format!("Direction output is missing {field}.rating"))?,
        rationale: text(row, "rationale")?,
    })
}

fn parse_direction(value: &Value) -> Result<BuildDirection, String> {
    let league = value
        .get("league_start")
        .ok_or_else(|| "Direction output is missing league_start".to_string())?;
    Ok(BuildDirection {
        direction_id: text(value, "direction_id")?,
        title: text(value, "title")?,
        concept: text(value, "concept")?,
        class_name: text(value, "class_name")?,
        ascendancy_id: text(value, "ascendancy_id")?,
        skill_id: text(value, "skill_id")?,
        mechanic_ids: texts(value, "mechanic_ids")?,
        support_ids: texts(value, "support_ids")?,
        passive_ids: texts(value, "passive_ids")?,
        item_base_ids: texts(value, "item_base_ids")?,
        mod_ids: texts(value, "mod_ids")?,
        unique_ids: texts(value, "unique_ids")?,
        damage_direction: text(value, "damage_direction")?,
        defense_direction: text(value, "defense_direction")?,
        mapping_viability: viability(value, "mapping_viability")?,
        boss_viability: viability(value, "boss_viability")?,
        budget: text(value, "budget")?,
        league_start: LeagueStart {
            viable: league
                .get("viable")
                .and_then(Value::as_bool)
                .ok_or_else(|| "Direction output is missing league_start.viable".to_string())?,
            rationale: text(league, "rationale")?,
        },
        strengths: texts(value, "strengths")?,
        weaknesses: texts(value, "weaknesses")?,
        critical_dependencies: texts(value, "critical_dependencies")?,
    })
}

fn parse_output(stdout: &[u8]) -> Result<DirectionResult, String> {
    let value: Value = serde_json::from_slice(stdout)
        .map_err(|error| format!("Core returned invalid direction JSON: {error}"))?;
    if value
        .pointer("/validation/schema_valid")
        .and_then(Value::as_bool)
        != Some(true)
        || value
            .pointer("/validation/entity_references_valid")
            .and_then(Value::as_bool)
            != Some(true)
        || value
            .pointer("/provider/is_live_ai")
            .and_then(Value::as_bool)
            != Some(true)
    {
        return Err("Core did not return validated live-AI directions".into());
    }
    let directions = value
        .get("directions")
        .and_then(Value::as_array)
        .ok_or_else(|| "Direction output is missing directions".to_string())?
        .iter()
        .map(parse_direction)
        .collect::<Result<Vec<_>, _>>()?;
    Ok(DirectionResult {
        provider_name: value
            .pointer("/provider/name")
            .and_then(Value::as_str)
            .ok_or_else(|| "Direction output is missing provider name".to_string())?
            .into(),
        quality_mode: text(&value, "quality_mode")?,
        attempts: value
            .get("attempts")
            .and_then(Value::as_i64)
            .ok_or_else(|| "Direction output is missing attempts".to_string())?,
        request_bytes: value
            .get("request_bytes")
            .and_then(Value::as_i64)
            .ok_or_else(|| "Direction output is missing request size".to_string())?,
        directions,
    })
}

pub fn generate_directions(request: DirectionRequest) -> Result<DirectionResult, String> {
    validate_request(&request)?;
    let api_endpoint = format!("{}/api/chat", request.endpoint);
    let stdout = run_core_command(&[
        "directions-ollama",
        "--model",
        &request.model,
        "--endpoint",
        &api_endpoint,
        "--skill",
        &request.skill,
        "--playstyle",
        &request.playstyle,
        "--goal",
        &request.goal,
        "--budget",
        &request.budget,
        "--quality",
        &request.quality_mode,
    ])?;
    parse_output(&stdout)
}

#[cfg(test)]
mod tests {
    use super::*;

    fn request() -> DirectionRequest {
        DirectionRequest {
            skill: "Snipe".into(),
            playstyle: "Fast".into(),
            goal: "Mapping".into(),
            budget: "Cheap".into(),
            endpoint: "http://127.0.0.1:11434".into(),
            model: "qwen3:8b".into(),
            quality_mode: "balanced".into(),
        }
    }

    #[test]
    fn rejects_non_local_endpoint() {
        let mut value = request();
        value.endpoint = "https://example.com".into();
        assert_eq!(
            validate_request(&value).unwrap_err(),
            "Only the local Ollama endpoint is supported"
        );
    }

    #[test]
    fn rejects_command_like_model_name() {
        let mut value = request();
        value.model = "qwen; calc.exe".into();
        assert_eq!(
            validate_request(&value).unwrap_err(),
            "Invalid Ollama model name"
        );
    }
}
