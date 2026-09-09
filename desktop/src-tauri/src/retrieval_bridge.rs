use crate::core_bridge::run_core_command;
use serde::{Deserialize, Serialize};
use serde_json::Value;

const GROUPS: [&str; 7] = [
    "mechanics",
    "supports",
    "passives",
    "ascendancies",
    "item_bases",
    "mods",
    "uniques",
];

#[derive(Debug, Deserialize)]
#[serde(rename_all = "camelCase")]
pub struct RetrievalRequest {
    skill: String,
    playstyle: String,
    goal: String,
    budget: String,
}

#[derive(Debug, Serialize)]
#[serde(rename_all = "camelCase")]
pub struct CandidatePreview {
    id: String,
    name: String,
    score: i64,
    reasons: Vec<String>,
}

#[derive(Debug, Serialize)]
#[serde(rename_all = "camelCase")]
pub struct CandidateGroup {
    category: String,
    count: usize,
    top: Vec<CandidatePreview>,
}

#[derive(Debug, Serialize)]
#[serde(rename_all = "camelCase")]
pub struct RetrievalSummary {
    skill_name: String,
    playstyle: String,
    goal: String,
    budget: String,
    serialized_bytes: i64,
    total_candidates: usize,
    groups: Vec<CandidateGroup>,
}

fn require_choice(value: &str, allowed: &[&str], field: &str) -> Result<(), String> {
    if allowed.contains(&value) {
        Ok(())
    } else {
        Err(format!("Unsupported {field} value"))
    }
}

fn validate_request(request: &RetrievalRequest) -> Result<(), String> {
    require_choice(&request.skill, &["Snipe"], "skill")?;
    require_choice(
        &request.playstyle,
        &["Fast", "Balanced", "Defensive"],
        "playstyle",
    )?;
    require_choice(&request.goal, &["Mapping", "Bossing", "Hybrid"], "goal")?;
    require_choice(&request.budget, &["Cheap", "Medium", "Expensive"], "budget")
}

fn parse_candidate(candidate: &Value) -> Result<CandidatePreview, String> {
    let id = candidate.get("id").and_then(Value::as_str);
    let name = candidate.get("name").and_then(Value::as_str);
    let score = candidate.get("score").and_then(Value::as_i64);
    let reasons = candidate.get("reasons").and_then(Value::as_array);
    match (id, name, score, reasons) {
        (Some(id), Some(name), Some(score), Some(reasons)) => Ok(CandidatePreview {
            id: id.into(),
            name: name.into(),
            score,
            reasons: reasons
                .iter()
                .map(|reason| {
                    reason
                        .as_str()
                        .map(String::from)
                        .ok_or_else(|| "Candidate contains a malformed reason".to_string())
                })
                .collect::<Result<Vec<_>, _>>()?,
        }),
        _ => Err("Candidate retrieval returned a malformed candidate".into()),
    }
}

fn required_string(value: &Value, pointer: &str) -> Result<String, String> {
    value
        .pointer(pointer)
        .and_then(Value::as_str)
        .map(String::from)
        .ok_or_else(|| format!("Retrieval output is missing {pointer}"))
}

fn parse_retrieval_output(stdout: &[u8]) -> Result<RetrievalSummary, String> {
    let value: Value = serde_json::from_slice(stdout)
        .map_err(|error| format!("Core returned invalid retrieval JSON: {error}"))?;
    let intent = value
        .get("intent")
        .ok_or_else(|| "Retrieval output is missing intent".to_string())?;
    let candidates = value
        .get("candidates")
        .and_then(Value::as_object)
        .ok_or_else(|| "Retrieval output is missing candidates".to_string())?;
    let mut groups = Vec::new();
    for category in GROUPS {
        let rows = candidates
            .get(category)
            .and_then(Value::as_array)
            .ok_or_else(|| format!("Retrieval output is missing {category}"))?;
        let top = rows
            .iter()
            .take(3)
            .map(parse_candidate)
            .collect::<Result<Vec<_>, _>>()?;
        groups.push(CandidateGroup {
            category: category.into(),
            count: rows.len(),
            top,
        });
    }
    let total_candidates = groups.iter().map(|group| group.count).sum();
    Ok(RetrievalSummary {
        skill_name: value
            .pointer("/skill/name")
            .and_then(Value::as_str)
            .ok_or_else(|| "Retrieval output is missing skill name".to_string())?
            .into(),
        playstyle: required_string(intent, "/playstyle")?,
        goal: required_string(intent, "/goal")?,
        budget: required_string(intent, "/budget")?,
        serialized_bytes: value
            .pointer("/debug/serialized_bytes")
            .and_then(Value::as_i64)
            .ok_or_else(|| "Retrieval output is missing serialized size".to_string())?,
        total_candidates,
        groups,
    })
}

pub fn retrieve_candidates(request: RetrievalRequest) -> Result<RetrievalSummary, String> {
    validate_request(&request)?;
    let stdout = run_core_command(&[
        "retrieve",
        "--skill",
        &request.skill,
        "--playstyle",
        &request.playstyle,
        "--goal",
        &request.goal,
        "--budget",
        &request.budget,
    ])?;
    parse_retrieval_output(&stdout)
}

#[cfg(test)]
mod tests {
    use super::*;

    fn fast_mapping() -> RetrievalRequest {
        RetrievalRequest {
            skill: "Snipe".into(),
            playstyle: "Fast".into(),
            goal: "Mapping".into(),
            budget: "Cheap".into(),
        }
    }

    #[test]
    fn reads_bounded_real_candidates() {
        let summary = retrieve_candidates(fast_mapping()).expect("real retrieval should pass");
        assert_eq!(summary.skill_name, "Snipe");
        assert!(summary.total_candidates <= 65);
        assert_eq!(summary.groups.len(), 7);
        assert!(summary.groups.iter().all(|group| group.top.len() <= 3));
        assert!(summary.serialized_bytes < 50_000);
    }

    #[test]
    fn rejects_values_outside_the_frontend_contract() {
        let mut request = fast_mapping();
        request.skill = "../../invented".into();
        assert_eq!(
            retrieve_candidates(request).expect_err("invalid skill must fail"),
            "Unsupported skill value"
        );
    }
}
