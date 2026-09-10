use serde::Serialize;
use serde_json::Value;
use std::io::Write;
use std::path::{Path, PathBuf};
use std::process::Command;
use std::process::Stdio;

#[cfg(windows)]
use std::os::windows::process::CommandExt;

#[cfg(windows)]
const CREATE_NO_WINDOW: u32 = 0x08000000;

#[derive(Debug, PartialEq, Serialize)]
#[serde(rename_all = "camelCase")]
pub struct CoreStatus {
    pub validation_checks: usize,
    pub passed_checks: usize,
    pub snipe_skills: i64,
    pub passive_nodes: i64,
    pub bow_bases: i64,
    pub provenance_files: i64,
}

fn looks_like_project_root(path: &Path) -> bool {
    path.join("pyproject.toml").is_file()
        && path.join("src/poe2_builder/cli.py").is_file()
        && path.join("data/poe2.db").is_file()
}

fn resolve_project_root() -> Result<PathBuf, String> {
    if let Ok(configured) = std::env::var("POE2_BUILDER_ROOT") {
        let path = PathBuf::from(configured);
        if looks_like_project_root(&path) {
            return Ok(path);
        }
        return Err("POE2_BUILDER_ROOT does not contain the expected read-only core files".into());
    }
    if let Ok(current) = std::env::current_dir() {
        for candidate in current.ancestors() {
            if looks_like_project_root(candidate) {
                return Ok(candidate.to_path_buf());
            }
        }
    }
    let development_root = Path::new(env!("CARGO_MANIFEST_DIR")).join("../..");
    if looks_like_project_root(&development_root) {
        return development_root
            .canonicalize()
            .map_err(|error| format!("Could not resolve development core path: {error}"));
    }
    Err("Could not locate the PoE2 deterministic core".into())
}

pub(crate) fn run_core_command(args: &[&str]) -> Result<Vec<u8>, String> {
    let root = resolve_project_root()?;
    let python = std::env::var("POE2_BUILDER_PYTHON").unwrap_or_else(|_| "python".into());
    let mut command = Command::new(python);
    command
        .args(["-m", "poe2_builder.cli"])
        .args(args)
        .current_dir(&root)
        .env("PYTHONPATH", root.join("src"));
    #[cfg(windows)]
    command.creation_flags(CREATE_NO_WINDOW);
    let output = command
        .output()
        .map_err(|error| format!("Could not start the deterministic core: {error}"))?;
    if !output.status.success() {
        let stderr = String::from_utf8_lossy(&output.stderr);
        return Err(format!(
            "Deterministic core command failed: {}",
            core_error_summary(&stderr)
        ));
    }
    Ok(output.stdout)
}

pub(crate) fn run_core_command_with_input(args: &[&str], input: &[u8]) -> Result<Vec<u8>, String> {
    let root = resolve_project_root()?;
    let python = std::env::var("POE2_BUILDER_PYTHON").unwrap_or_else(|_| "python".into());
    let mut command = Command::new(python);
    command
        .args(["-m", "poe2_builder.cli"])
        .args(args)
        .current_dir(&root)
        .env("PYTHONPATH", root.join("src"))
        .stdin(Stdio::piped())
        .stdout(Stdio::piped())
        .stderr(Stdio::piped());
    #[cfg(windows)]
    command.creation_flags(CREATE_NO_WINDOW);
    let mut child = command
        .spawn()
        .map_err(|error| format!("Could not start the deterministic core: {error}"))?;
    child
        .stdin
        .take()
        .ok_or_else(|| "Could not open deterministic core input".to_string())?
        .write_all(input)
        .map_err(|error| format!("Could not write deterministic core input: {error}"))?;
    let output = child
        .wait_with_output()
        .map_err(|error| format!("Could not read deterministic core output: {error}"))?;
    if !output.status.success() {
        let stderr = String::from_utf8_lossy(&output.stderr);
        return Err(format!(
            "Deterministic core command failed: {}",
            core_error_summary(&stderr)
        ));
    }
    Ok(output.stdout)
}

fn core_error_summary(stderr: &str) -> &str {
    stderr
        .lines()
        .rev()
        .find(|line| !line.trim().is_empty())
        .map(str::trim)
        .unwrap_or("Unknown core error")
}

fn actual_for(rows: &[Value], check: &str) -> Result<i64, String> {
    rows.iter()
        .find(|row| row.get("check").and_then(Value::as_str) == Some(check))
        .and_then(|row| row.get("actual"))
        .and_then(Value::as_i64)
        .ok_or_else(|| format!("Core validation output is missing {check:?}"))
}

fn parse_validation_output(stdout: &[u8]) -> Result<CoreStatus, String> {
    let rows: Vec<Value> = serde_json::from_slice(stdout)
        .map_err(|error| format!("Core returned invalid validation JSON: {error}"))?;
    let passed_checks = rows
        .iter()
        .filter(|row| row.get("passed").and_then(Value::as_bool) == Some(true))
        .count();
    if rows.is_empty() || passed_checks != rows.len() {
        return Err(format!(
            "Core validation failed: {passed_checks}/{} checks passed",
            rows.len()
        ));
    }
    Ok(CoreStatus {
        validation_checks: rows.len(),
        passed_checks,
        snipe_skills: actual_for(&rows, "Snipe exists")?,
        passive_nodes: actual_for(&rows, "Passive data available")?,
        bow_bases: actual_for(&rows, "Bow bases queryable")?,
        provenance_files: actual_for(&rows, "Data provenance recorded")?,
    })
}

pub fn read_core_status() -> Result<CoreStatus, String> {
    parse_validation_output(&run_core_command(&["validate"])?)
}

#[cfg(test)]
mod tests {
    use super::*;

    #[test]
    fn reads_the_real_python_core_without_mutation() {
        let status = read_core_status().expect("real core status should load");
        assert_eq!(status.validation_checks, status.passed_checks);
        assert_eq!(status.snipe_skills, 1);
        assert!(status.passive_nodes >= 5_000);
        assert!(status.bow_bases >= 35);
        assert_eq!(status.provenance_files, 7);
    }

    #[test]
    fn rejects_a_partial_or_failed_validation_result() {
        let error =
            parse_validation_output(br#"[{"check":"Snipe exists","actual":1,"passed":false}]"#)
                .expect_err("failed validation must not be summarized as healthy");
        assert!(error.contains("0/1 checks passed"));
    }

    #[test]
    fn reports_only_the_actionable_python_error() {
        let stderr = "Traceback (most recent call last):\n  noisy frame\nFullBuildValidationError: narrative contains a numeric claim\n";
        assert_eq!(
            core_error_summary(stderr),
            "FullBuildValidationError: narrative contains a numeric claim"
        );
    }
}
