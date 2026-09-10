mod build_bridge;
mod core_bridge;
mod direction_bridge;
mod retrieval_bridge;

#[tauri::command]
async fn core_status() -> Result<core_bridge::CoreStatus, String> {
    run_blocking(core_bridge::read_core_status).await
}

#[tauri::command]
async fn retrieve_candidates(
    request: retrieval_bridge::RetrievalRequest,
) -> Result<retrieval_bridge::RetrievalSummary, String> {
    run_blocking(move || retrieval_bridge::retrieve_candidates(request)).await
}

#[tauri::command]
async fn generate_directions(
    request: direction_bridge::DirectionRequest,
) -> Result<direction_bridge::DirectionResult, String> {
    run_blocking(move || direction_bridge::generate_directions(request)).await
}

#[tauri::command]
async fn generate_full_build(
    request: build_bridge::FullBuildRequest,
) -> Result<serde_json::Value, String> {
    run_blocking(move || build_bridge::generate_full_build(request)).await
}

#[tauri::command]
async fn answer_build_question(
    request: build_bridge::ChatRequest,
) -> Result<serde_json::Value, String> {
    run_blocking(move || build_bridge::answer_build_question(request)).await
}

async fn run_blocking<T, F>(operation: F) -> Result<T, String>
where
    T: Send + 'static,
    F: FnOnce() -> Result<T, String> + Send + 'static,
{
    tauri::async_runtime::spawn_blocking(operation)
        .await
        .map_err(|error| format!("Background task failed: {error}"))?
}

#[cfg_attr(mobile, tauri::mobile_entry_point)]
pub fn run() {
    tauri::Builder::default()
        .invoke_handler(tauri::generate_handler![
            core_status,
            retrieve_candidates,
            generate_directions,
            generate_full_build,
            answer_build_question
        ])
        .run(tauri::generate_context!())
        .expect("error while running PoE2 Build Architect");
}
