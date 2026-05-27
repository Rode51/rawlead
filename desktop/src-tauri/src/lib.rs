#[tauri::command]
fn radar_env_port() -> Option<u16> {
    std::env::var("RADAR_CONTROL_PORT")
        .ok()
        .and_then(|s| s.trim().parse().ok())
}

#[tauri::command]
fn radar_env_profile() -> Option<String> {
    std::env::var("RADAR_PROFILE")
        .ok()
        .map(|s| s.trim().to_ascii_lowercase())
        .filter(|s| !s.is_empty())
}

#[cfg_attr(mobile, tauri::mobile_entry_point)]
pub fn run() {
    tauri::Builder::default()
        .plugin(tauri_plugin_http::init())
        .plugin(tauri_plugin_opener::init())
        .invoke_handler(tauri::generate_handler![radar_env_port, radar_env_profile])
        .run(tauri::generate_context!())
        .expect("error while running tauri application");
}
