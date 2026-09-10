use crate::core_bridge::run_core_command_with_input;
use serde::Deserialize;
use serde_json::{json, Value};

#[derive(Debug, Deserialize)]
#[serde(rename_all = "camelCase")]
pub struct FullBuildRequest {
    endpoint: String,
    model: String,
    direction: Value,
}

#[derive(Debug, Deserialize)]
#[serde(rename_all = "camelCase")]
pub struct ChatMessage {
    role: String,
    content: String,
}

#[derive(Debug, Deserialize)]
#[serde(rename_all = "camelCase")]
pub struct ChatRequest {
    endpoint: String,
    model: String,
    direction: Value,
    build: Value,
    intent: Value,
    question: String,
    history: Vec<ChatMessage>,
}

fn provider_args(endpoint: &str, model: &str) -> Result<(String, String), String> {
    if endpoint != "http://127.0.0.1:11434" && endpoint != "http://localhost:11434" {
        return Err("Only the local Ollama endpoint is supported".into());
    }
    if model.is_empty()
        || model.len() > 100
        || !model
            .chars()
            .all(|character| character.is_ascii_alphanumeric() || ".:_-/".contains(character))
    {
        return Err("Invalid Ollama model name".into());
    }
    Ok((format!("{endpoint}/api/chat"), model.into()))
}

fn parse_validated(stdout: &[u8], kind: &str) -> Result<Value, String> {
    let value: Value = serde_json::from_slice(stdout)
        .map_err(|error| format!("Core returned invalid {kind} JSON: {error}"))?;
    if kind == "full-build" {
        let validation = value
            .get("validation")
            .and_then(Value::as_object)
            .ok_or_else(|| "Full build output is missing validation".to_string())?;
        if validation.is_empty() || !validation.values().all(|flag| flag.as_bool() == Some(true)) {
            return Err("Core did not return a fully validated build".into());
        }
    }
    Ok(value)
}

pub fn generate_full_build(request: FullBuildRequest) -> Result<Value, String> {
    let (endpoint, model) = provider_args(&request.endpoint, &request.model)?;
    let input = serde_json::to_vec(&json!({"direction": request.direction}))
        .map_err(|error| format!("Could not serialize full-build input: {error}"))?;
    let stdout = run_core_command_with_input(
        &[
            "full-build-ollama-stdin",
            "--model",
            &model,
            "--endpoint",
            &endpoint,
        ],
        &input,
    )?;
    parse_validated(&stdout, "full-build")
}

pub fn answer_build_question(request: ChatRequest) -> Result<Value, String> {
    let (endpoint, model) = provider_args(&request.endpoint, &request.model)?;
    if request.question.trim().is_empty()
        || request.question.len() > 2_000
        || request.history.len() > 12
    {
        return Err("Chat question or history is outside the supported bounds".into());
    }
    let history: Vec<Value> = request
        .history
        .into_iter()
        .map(|message| {
            json!({
                "role": message.role, "content": message.content
            })
        })
        .collect();
    let input = serde_json::to_vec(&json!({
        "direction": request.direction, "build": request.build,
        "intent": request.intent, "question": request.question, "history": history
    }))
    .map_err(|error| format!("Could not serialize build-chat input: {error}"))?;
    let stdout = run_core_command_with_input(
        &[
            "build-chat-ollama-stdin",
            "--model",
            &model,
            "--endpoint",
            &endpoint,
        ],
        &input,
    )?;
    parse_validated(&stdout, "build-chat")
}

#[cfg(test)]
mod tests {
    use super::*;

    #[test]
    fn rejects_remote_provider_for_build_and_chat() {
        assert!(provider_args("https://example.com", "qwen3:8b").is_err());
    }
}
