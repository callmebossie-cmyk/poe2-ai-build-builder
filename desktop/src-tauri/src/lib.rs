mod core_bridge;

#[tauri::command]
fn core_status() -> Result<core_bridge::CoreStatus, String> {
    core_bridge::read_core_status()
}

#[cfg_attr(mobile, tauri::mobile_entry_point)]
pub fn run() {
    tauri::Builder::default()
        .invoke_handler(tauri::generate_handler![core_status])
        .run(tauri::generate_context!())
        .expect("error while running PoE2 Build Architect");
}
