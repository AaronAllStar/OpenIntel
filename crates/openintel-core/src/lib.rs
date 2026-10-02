pub mod db;
pub mod id_validation;

use pyo3::prelude::*;
use std::collections::HashMap;

/// Validate a single national ID string against supported international algorithms.
/// Returns a list of dictionaries with keys "scheme", "country", and "standard".
#[pyfunction]
pub fn validate_national_id(raw_id: &str) -> Vec<HashMap<String, String>> {
    let results = id_validation::validate_single(raw_id);
    results
        .into_iter()
        .map(|r| {
            let mut map = HashMap::with_capacity(3);
            map.insert("scheme".to_string(), r.scheme);
            map.insert("country".to_string(), r.country);
            map.insert("standard".to_string(), r.standard);
            map
        })
        .collect()
}

/// Concurrently validate a batch of national IDs using Rayon multi-threading.
/// Returns a list of lists of dictionaries matching the input order.
#[pyfunction]
pub fn validate_batch(raw_ids: Vec<String>) -> Vec<Vec<HashMap<String, String>>> {
    let results = id_validation::validate_batch(&raw_ids);
    results
        .into_iter()
        .map(|batch| {
            batch
                .into_iter()
                .map(|r| {
                    let mut map = HashMap::with_capacity(3);
                    map.insert("scheme".to_string(), r.scheme);
                    map.insert("country".to_string(), r.country);
                    map.insert("standard".to_string(), r.standard);
                    map
                })
                .collect()
        })
        .collect()
}

/// Report the status and metadata of the OpenIntel PostgreSQL Rust engine.
#[pyfunction]
pub fn postgres_engine_info() -> String {
    "OpenIntel Rust Engine (PostgreSQL sqlx 0.8 / Tokio / Rayon / PyO3 0.22)".to_string()
}

/// PyO3 Python extension module declaration.
#[pymodule]
fn openintel_core(m: &Bound<'_, PyModule>) -> PyResult<()> {
    m.add_function(wrap_pyfunction!(validate_national_id, m)?)?;
    m.add_function(wrap_pyfunction!(validate_batch, m)?)?;
    m.add_function(wrap_pyfunction!(postgres_engine_info, m)?)?;
    Ok(())
}
